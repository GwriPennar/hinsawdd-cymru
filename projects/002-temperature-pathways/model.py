"""Project 002: transparent observed-trend temperature pathways for Wales."""
from __future__ import annotations
import argparse, json, math, re
from dataclasses import asdict, dataclass
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

PROJECT_DIR=Path(__file__).resolve().parent
REPOSITORY_DIR=PROJECT_DIR.parents[1]
P1=REPOSITORY_DIR/'projects/001-rolling-temperature'
SOURCE_CSV=P1/'data/derived/august_to_july_mean_temperature.csv'
SOURCE_SUMMARY=P1/'data/derived/summary.json'
SOURCE_VERIFICATION=P1/'data/derived/independent_verification.json'
DERIVED_DIR=PROJECT_DIR/'data/derived'; FIGURES_DIR=PROJECT_DIR/'figures'; README_PATH=PROJECT_DIR/'README.md'
RESULT_START='<!-- BEGIN GENERATED RESULT -->'; RESULT_END='<!-- END GENERATED RESULT -->'; YEAR_CENTRE=2000.0

@dataclass(frozen=True)
class ModelConfig:
    fit_start_end_year:int=1970; projection_end_year:int=2125; bootstrap_replicates:int=2000
    bootstrap_block_length:int=5; random_seed:int=20260802; backtest_horizon_years:int=10
    backtest_cutoffs:tuple[int,...]=(1990,2000,2010,2015)

@dataclass(frozen=True)
class LinearFit:
    intercept_at_2000_c:float; slope_c_per_year:float; r_squared:float
    residual_standard_error_c:float; observation_count:int; first_end_year:int; last_end_year:int
    @property
    def slope_c_per_decade(self): return self.slope_c_per_year*10
    def predict_anomaly(self, years): return self.intercept_at_2000_c+self.slope_c_per_year*(np.asarray(years)-YEAR_CENTRE)

def _json(path:Path):
    if not path.exists(): raise FileNotFoundError(f'Missing required Project 001 output: {path}')
    return json.loads(path.read_text(encoding='utf-8'))

def load_validated_inputs(source_csv=SOURCE_CSV,source_summary=SOURCE_SUMMARY,source_verification=SOURCE_VERIFICATION):
    if not source_csv.exists(): raise FileNotFoundError(f'Missing {source_csv}. Generate Project 001 first.')
    data=pd.read_csv(source_csv); summary=_json(source_summary); verification=_json(source_verification)
    required={'period','start_date','end_date','end_year','mean_temperature_c','status'}
    missing=required.difference(data.columns)
    if missing: raise ValueError(f'Project 001 series is missing columns: {sorted(missing)}')
    data=data.sort_values('end_year').reset_index(drop=True); years=data.end_year.to_numpy(int)
    if data.empty or not np.array_equal(years,np.arange(years[0],years[-1]+1)): raise ValueError('Project 001 series must be non-empty and continuous')
    if data.end_year.duplicated().any(): raise ValueError('Project 001 end years must be unique')
    if data.iloc[0].period!='1884-08 to 1885-07' or data.iloc[-1].period!='2025-08 to 2026-07': raise ValueError('Unexpected Project 001 period boundary')
    if verification.get('verification_status')!='pass': raise ValueError('Project 001 independent verification has not passed')
    if verification.get('primary_summary_comparison')!='pass': raise ValueError('Project 001 primary-summary comparison has not passed')
    if verification.get('source_sha256')!=summary.get('source_snapshot_sha256'): raise ValueError('Project 001 source hashes disagree')
    if not math.isclose(float(data.iloc[-1].mean_temperature_c),float(summary['period_mean_central_c']),abs_tol=1e-6): raise ValueError('Project 001 latest period disagrees with summary')
    if int(summary['rank_among_august_to_july_periods'])!=1: raise ValueError('Project 001 retained rank is not 1')
    ref=float(summary['derived_reference_1991_2020_c'])
    if not np.isfinite(ref): raise ValueError('Project 001 reference mean must be finite')
    data['temperature_anomaly_c']=data.mean_temperature_c-ref
    return data,summary,verification

def fit_linear_trend(frame):
    if len(frame)<3: raise ValueError('At least three observations are required')
    years=frame.end_year.to_numpy(float); values=frame.temperature_anomaly_c.to_numpy(float)
    if not np.isfinite(years).all() or not np.isfinite(values).all(): raise ValueError('Regression inputs must be finite')
    x=years-YEAR_CENTRE; A=np.c_[np.ones(len(x)),x]; intercept,slope=np.linalg.lstsq(A,values,rcond=None)[0]
    residuals=values-(intercept+slope*x); rss=float(np.sum(residuals**2)); tss=float(np.sum((values-values.mean())**2))
    return LinearFit(float(intercept),float(slope),1-rss/tss,math.sqrt(rss/(len(values)-2)),len(frame),int(years.min()),int(years.max()))

def theil_sen_fit(frame):
    years=frame.end_year.to_numpy(float); values=frame.temperature_anomaly_c.to_numpy(float); slopes=[]
    for i in range(len(years)-1): slopes.extend(((values[i+1:]-values[i])/(years[i+1:]-years[i])).tolist())
    slope=float(np.median(slopes)); intercept=float(np.median(values-slope*(years-YEAR_CENTRE)))
    residuals=values-(intercept+slope*(years-YEAR_CENTRE)); rss=float(np.sum(residuals**2)); tss=float(np.sum((values-values.mean())**2))
    return LinearFit(intercept,slope,1-rss/tss,math.sqrt(rss/max(1,len(values)-2)),len(frame),int(years.min()),int(years.max()))

def moving_block_bootstrap(frame,projection_years,config):
    fit=fit_linear_trend(frame); years=frame.end_year.to_numpy(float); values=frame.temperature_anomaly_c.to_numpy(float)
    fitted=np.asarray(fit.predict_anomaly(years),float); residuals=values-fitted; residuals-=residuals.mean(); n=len(residuals)
    if not 1<=config.bootstrap_block_length<=n: raise ValueError('Invalid bootstrap block length')
    if config.bootstrap_replicates<100: raise ValueError('At least 100 bootstrap replicates are required')
    rng=np.random.default_rng(config.random_seed); A=np.c_[np.ones(n),years-YEAR_CENTRE]; xp=projection_years-YEAR_CENTRE
    predictions=np.empty((config.bootstrap_replicates,len(projection_years)))
    for r in range(config.bootstrap_replicates):
        sample=[]
        while len(sample)<n:
            start=int(rng.integers(0,n)); idx=(start+np.arange(config.bootstrap_block_length))%n; sample.extend(residuals[idx].tolist())
        intercept,slope=np.linalg.lstsq(A,fitted+np.asarray(sample[:n]),rcond=None)[0]; predictions[r]=intercept+slope*xp
    return tuple(np.quantile(predictions,[.025,.5,.975],axis=0))

def run_backtests(published,config):
    rows=[]
    for cutoff in config.backtest_cutoffs:
        train=published[published.end_year.between(config.fit_start_end_year,cutoff)]
        test=published[published.end_year.between(cutoff+1,cutoff+config.backtest_horizon_years)]
        if len(train)<20 or len(test)!=config.backtest_horizon_years: raise ValueError(f'Backtest {cutoff} is incomplete')
        fit=fit_linear_trend(train); predicted=np.asarray(fit.predict_anomaly(test.end_year.to_numpy()),float); actual=test.temperature_anomaly_c.to_numpy(float)
        rows.append({'training_end_year':cutoff,'test_start_year':cutoff+1,'test_end_year':cutoff+config.backtest_horizon_years,'training_observations':len(train),'actual_test_mean_anomaly_c':float(actual.mean()),'predicted_test_mean_anomaly_c':float(predicted.mean()),'mean_anomaly_error_c':float(predicted.mean()-actual.mean()),'annual_mae_c':float(np.mean(np.abs(predicted-actual))),'annual_rmse_c':float(np.sqrt(np.mean((predicted-actual)**2)))})
    return pd.DataFrame(rows)

def prepare_projection(data,summary,config):
    published=data[data.status=='published-inputs'].copy(); modern=published[published.end_year>=config.fit_start_end_year].copy()
    primary=fit_linear_trend(modern); full=fit_linear_trend(published); robust=theil_sen_fit(modern)
    years=np.arange(int(data.end_year.min()),config.projection_end_year+1); lower,median,upper=moving_block_bootstrap(modern,years,config); ref=float(summary['derived_reference_1991_2020_c'])
    projection=pd.DataFrame({'end_year':years,'primary_anomaly_c':primary.predict_anomaly(years),'primary_mean_temperature_c':primary.predict_anomaly(years)+ref,'bootstrap_median_mean_temperature_c':median+ref,'bootstrap_95_lower_mean_temperature_c':lower+ref,'bootstrap_95_upper_mean_temperature_c':upper+ref,'full_record_mean_temperature_c':full.predict_anomaly(years)+ref,'theil_sen_mean_temperature_c':robust.predict_anomaly(years)+ref})
    projection['period_kind']=np.where(projection.end_year<=primary.last_end_year,'historical-fit','extrapolation')
    backtests=run_backtests(published,config); milestones={}
    for year in (2050,2100,config.projection_end_year):
        row=projection.loc[projection.end_year==year].iloc[0]; milestones[str(year)]={'primary_mean_temperature_c':float(row.primary_mean_temperature_c),'bootstrap_95_lower_c':float(row.bootstrap_95_lower_mean_temperature_c),'bootstrap_95_upper_c':float(row.bootstrap_95_upper_mean_temperature_c),'full_record_sensitivity_c':float(row.full_record_mean_temperature_c),'theil_sen_sensitivity_c':float(row.theil_sen_mean_temperature_c)}
    latest=data.iloc[-1]
    model_summary={'model_status':'illustrative-statistical-extrapolation','warning':'This is a continuation of observed statistical trends, not a physical climate forecast or emissions-scenario projection.','configuration':asdict(config),'source_project':'001-rolling-temperature','source_snapshot_sha256':summary['source_snapshot_sha256'],'source_last_updated':summary['source_last_updated'],'source_last_published_month':'2026-06','reference_mean_1991_2020_c':ref,'latest_context_period':str(latest.period),'latest_context_mean_c':float(latest.mean_temperature_c),'latest_context_status':str(latest.status),'latest_context_used_for_training':False,'training_boundary_note':'Only published-input periods are fitted; the provisional 2025-26 point is context only.','primary_fit':{**asdict(primary),'slope_c_per_decade':primary.slope_c_per_decade},'full_record_sensitivity_fit':{**asdict(full),'slope_c_per_decade':full.slope_c_per_decade},'theil_sen_sensitivity_fit':{**asdict(robust),'slope_c_per_decade':robust.slope_c_per_decade},'milestones':milestones,'backtest_summary':{'origins':len(backtests),'mean_absolute_ten_year_mean_error_c':float(backtests.mean_anomaly_error_c.abs().mean()),'mean_annual_mae_c':float(backtests.annual_mae_c.mean()),'mean_annual_rmse_c':float(backtests.annual_rmse_c.mean())}}
    return projection,model_summary,backtests

def make_figure(data,projection,summary,output_base):
    sns.set_theme(style='whitegrid',context='talk'); plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','axes.edgecolor':'#4b5563','axes.linewidth':1.1}); palette=sns.color_palette('deep',10)
    fig,ax=plt.subplots(figsize=(16,9),dpi=100); fig.patch.set_facecolor('white'); ax.set_facecolor('white')
    published=data[data.status=='published-inputs']; provisional=data[data.status!='published-inputs']; years=published.end_year.to_numpy(int); values=published.mean_temperature_c.to_numpy(float); rolling=published.mean_temperature_c.rolling(10,min_periods=10).mean(); last=int(summary['primary_fit']['last_end_year'])
    future=projection[projection.end_year>=last]; history=projection[projection.end_year.between(int(summary['primary_fit']['first_end_year']),last)]
    ax.plot(years,values,color='#8a94a6',lw=1,alpha=.7,marker='o',ms=2.5,label='Published August-to-July periods',zorder=2)
    ax.plot(years,rolling,color=palette[0],lw=3.2,label='Trailing 10-period average',zorder=4)
    ax.plot(history.end_year,history.primary_mean_temperature_c,color=palette[3],lw=2.4,label='Primary linear fit, published periods ending 1970 onward',zorder=5)
    ax.fill_between(future.end_year,future.bootstrap_95_lower_mean_temperature_c,future.bootstrap_95_upper_mean_temperature_c,color=palette[3],alpha=.17,label='95% moving-block bootstrap trend-fit range',zorder=1)
    ax.plot(future.end_year,future.primary_mean_temperature_c,color=palette[3],lw=3,ls='--',label='Primary statistical extrapolation',zorder=5)
    ax.plot(future.end_year,future.full_record_mean_temperature_c,color=palette[2],lw=1.7,ls=':',label='Full-record OLS sensitivity',zorder=3)
    ax.plot(future.end_year,future.theil_sen_mean_temperature_c,color=palette[4],lw=1.7,ls='-.',label='Modern Theil-Sen sensitivity',zorder=3)
    if not provisional.empty: ax.scatter(provisional.end_year,provisional.mean_temperature_c,s=85,color=palette[1],edgecolor='white',lw=1,label='2025-26 illustrative context point, excluded from fit',zorder=8)
    ax.axvline(last,color='#6b7280',lw=1.2,ls='--'); ax.text(last+1.5,7.25,'Extrapolation begins',rotation=90,va='bottom',ha='left',color='#6b7280',fontsize=10)
    for year in (2050,2100):
        row=projection.loc[projection.end_year==year].iloc[0]; value=float(row.primary_mean_temperature_c); ax.scatter([year],[value],s=50,color=palette[3],zorder=7); ax.annotate(f'{year}: {value:.2f}°C',(year,value),xytext=(7,8),textcoords='offset points',fontsize=10.5,fontweight='bold',color=palette[3])
    ax.set_xlim(int(data.end_year.min())-1,int(projection.end_year.max())); ax.set_ylim(min(6.5,float(data.mean_temperature_c.min())-.4),max(float(projection.bootstrap_95_upper_mean_temperature_c.max())+.4,float(data.mean_temperature_c.max())+.4))
    ax.set_xlabel('August-to-July period end year'); ax.set_ylabel('Wales mean temperature (°C)'); ax.set_title('WALES TEMPERATURE PATHWAYS: A SIMPLE OBSERVED-TREND BASELINE',fontsize=21,fontweight='bold',pad=24)
    ax.text(.5,1.012,'Illustrative statistical continuation to 2125, not a physical climate forecast',transform=ax.transAxes,ha='center',va='bottom',fontsize=12.5); ax.legend(loc='upper left',ncol=2,fontsize=9.5,frameon=True,columnspacing=1.3,handlelength=3); ax.grid(True,ls=':',lw=.9,alpha=.68)
    fig.text(.065,.955,'Hinsawdd Cymru · Project 002',ha='left',va='top',fontsize=12.5,fontweight='bold'); fig.text(.94,.955,f"Source snapshot: {summary['source_last_updated']}",ha='right',va='top',fontsize=10.5)
    fig.text(.065,.018,'Data: Project 001 calculation from the Met Office Wales HadUK-Grid monthly areal series. The provisional 2025-26 point is displayed but excluded from fitting. Future lines assume the fitted statistical relationship continues unchanged.',ha='left',va='bottom',fontsize=8.8)
    fig.subplots_adjust(left=.08,right=.975,top=.84,bottom=.12); output_base.parent.mkdir(parents=True,exist_ok=True); png=output_base.with_suffix('.png'); svg=output_base.with_suffix('.svg'); fig.savefig(png,dpi=100,facecolor='white'); fig.savefig(svg,facecolor='white'); plt.close(fig); return png,svg

def _table(summary):
    p=summary['primary_fit']; m=summary['milestones']; b=summary['backtest_summary']
    return '\n'.join(['| Measure | Result |','|---|---:|',f"| Published observations used for primary fit | **{p['observation_count']}** |",f"| Primary fit period end years | **{p['first_end_year']}–{p['last_end_year']}** |",f"| Primary observed slope | **{p['slope_c_per_decade']:+.3f}°C per decade** |",f"| Primary linear-fit R² | **{p['r_squared']:.3f}** |",f"| Illustrative 2050 mean | **{m['2050']['primary_mean_temperature_c']:.2f}°C** |",f"| 2050 bootstrap trend-fit range | **{m['2050']['bootstrap_95_lower_c']:.2f} to {m['2050']['bootstrap_95_upper_c']:.2f}°C** |",f"| Illustrative 2100 mean | **{m['2100']['primary_mean_temperature_c']:.2f}°C** |",f"| 2100 bootstrap trend-fit range | **{m['2100']['bootstrap_95_lower_c']:.2f} to {m['2100']['bootstrap_95_upper_c']:.2f}°C** |",f"| Mean absolute error of ten-year mean hindcasts | **{b['mean_absolute_ten_year_mean_error_c']:.2f}°C** |",f"| Mean annual hindcast RMSE | **{b['mean_annual_rmse_c']:.2f}°C** |"])

def update_readme(summary):
    text=README_PATH.read_text(encoding='utf-8'); block=f"""{RESULT_START}
## Headline baseline result

> **This is not a physical climate forecast.** It is a transparent test of what happens if the observed modern linear relationship continues unchanged.

{_table(summary)}

The primary fit excludes the provisional 2025–26 scenario point. It uses only published-input August-to-July periods ending from **{summary['primary_fit']['first_end_year']} to {summary['primary_fit']['last_end_year']}**. The latest provisional point is retained on the chart as context.

The wide difference between the modern-period and full-record sensitivity lines is itself an important result: long-range straight-line extrapolation depends heavily on the chosen historical window. Project 002 therefore publishes this model as a **baseline for comparison**, not as the preferred estimate of Wales's physical future climate.
{RESULT_END}"""
    pattern=re.compile(re.escape(RESULT_START)+r'.*?'+re.escape(RESULT_END),re.DOTALL)
    if not pattern.search(text): raise ValueError('Project 002 README generated-result markers are missing')
    README_PATH.write_text(pattern.sub(block,text),encoding='utf-8')

def run(config=ModelConfig(),*,source_csv=SOURCE_CSV,source_summary=SOURCE_SUMMARY,source_verification=SOURCE_VERIFICATION,update_project_readme=True):
    data,summary,verification=load_validated_inputs(source_csv,source_summary,source_verification); projection,model_summary,backtests=prepare_projection(data,summary,config); DERIVED_DIR.mkdir(parents=True,exist_ok=True); FIGURES_DIR.mkdir(parents=True,exist_ok=True)
    data.to_csv(DERIVED_DIR/'observed_august_to_july_input.csv',index=False,float_format='%.6f'); projection.to_csv(DERIVED_DIR/'linear_regression_projection.csv',index=False,float_format='%.6f'); backtests.to_csv(DERIVED_DIR/'backtest_results.csv',index=False,float_format='%.6f')
    (DERIVED_DIR/'source_verification_snapshot.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf-8'); png,svg=make_figure(data,projection,model_summary,FIGURES_DIR/'wales_temperature_pathways_linear_regression')
    def label(path):
        try: return str(path.relative_to(PROJECT_DIR))
        except ValueError: return str(path)
    model_summary['outputs']={'png':label(png),'svg':label(svg),'projection_csv':'data/derived/linear_regression_projection.csv','backtest_csv':'data/derived/backtest_results.csv'}
    (DERIVED_DIR/'model_summary.json').write_text(json.dumps(model_summary,indent=2)+'\n',encoding='utf-8')
    if update_project_readme: update_readme(model_summary)
    return model_summary

def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--fit-start',type=int,default=1970); parser.add_argument('--projection-end',type=int,default=2125); parser.add_argument('--bootstrap-replicates',type=int,default=2000); parser.add_argument('--bootstrap-block-length',type=int,default=5); parser.add_argument('--seed',type=int,default=20260802); parser.add_argument('--source-csv',type=Path,default=SOURCE_CSV); parser.add_argument('--source-summary',type=Path,default=SOURCE_SUMMARY); parser.add_argument('--source-verification',type=Path,default=SOURCE_VERIFICATION); parser.add_argument('--no-update-readme',action='store_true'); args=parser.parse_args()
    config=ModelConfig(args.fit_start,args.projection_end,args.bootstrap_replicates,args.bootstrap_block_length,args.seed); print(json.dumps(run(config,source_csv=args.source_csv,source_summary=args.source_summary,source_verification=args.source_verification,update_project_readme=not args.no_update_readme),indent=2))
if __name__=='__main__': main()
