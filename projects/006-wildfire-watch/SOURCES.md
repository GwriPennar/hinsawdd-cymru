# Project 006 primary-source register

Project 006 uses primary NASA/EOSDIS documentation for the satellite-data contract. Access dates should be updated when a live evidence snapshot is published.

## NASA FIRMS Area API

**NASA LANCE FIRMS — API / Area**  
https://firms.modaps.eosdis.nasa.gov/api/area/

Used for the live endpoint contract, source IDs, bounding-box order, optional date, 1–5 day request range and map-key requirement.

## NASA FIRMS API tutorial

**NASA LANCE FIRMS Fire Data Academy — FIRMS API use**  
https://firms.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html

Used to verify the VIIRS Area API field set and the documented conversion of `acq_date` + zero-padded `acq_time` into a datetime. The tutorial example exposes the standard VIIRS columns including latitude, longitude, confidence, version, FRP and day/night.

## VIIRS Collection 2 active-fire user guide

**NASA Earthdata — Collection 2 Visible Infrared Imaging Radiometer Suite (VIIRS) 375 m active fire product user guide**  
https://www.earthdata.nasa.gov/s3fs-public/2024-07/VIIRS_C2_AF-375m_User_Guide_1.0.pdf

Used for the scientific product boundary and platform mapping. The guide describes the 375 m products for S-NPP, NOAA-20 and NOAA-21 and identifies the platform-specific product families VNP14IMG, VJ114IMG and VJ214IMG.

## S-NPP VIIRS NRT product

**NASA Earthdata — VIIRS/NPP Active Fires 6-Min L2 Swath 375m NRT**  
https://www.earthdata.nasa.gov/data/catalog/lancemodis-vnp14img-nrt-2

Used to confirm that the S-NPP product is a near-real-time 375 m active-fire/thermal-anomaly product distributed through LANCE/FIRMS.

## NOAA-20 VIIRS NRT product

**NASA Earthdata — VIIRS/JPSS1 Active Fires 6-Min L2 Swath 375m NRT**  
https://www.earthdata.nasa.gov/data/catalog/lancemodis-vj114img-nrt-2

Used to confirm the NOAA-20/JPSS-1 375 m NRT active-fire product.

## FIRMS system description

**NASA Earthdata Wiki — Fire Information for Resource Management System (FIRMS)**  
https://wiki.earthdata.nasa.gov/spaces/FIRMS/pages/32079892/Fire+Information+for+Resource+Management+System+FIRMS

Used for the system-level description that FIRMS distributes near-real-time active-fire locations processed by LANCE with the VIIRS 375 m fire and thermal-anomaly algorithms.

## Citation / data-use boundary

NASA/EOSDIS source data remain subject to NASA's data-use and citation guidance. Project 006 code is MIT licensed with the rest of the repository; that does not relicense the upstream data or third-party map assets.

## Front-end libraries

The generated MVP map loads:

- Leaflet 1.9.4 from `unpkg.com`;
- Leaflet.markercluster 1.5.3 from `unpkg.com`;
- OpenStreetMap raster tiles from `tile.openstreetmap.org`.

These are presentation dependencies, not scientific data sources. A public production deployment should review their current licences/usage policies and may choose to self-host/pin assets.
