import cdsapi

dataset = "reanalysis-era5-land"
months= ["09", "10", "11", "12"]
for month in months:
    request = {
        "variable": [
            # "2m_dewpoint_temperature",
            # "2m_temperature",
            # "skin_temperature",
            # "snow_density",
            # "snowfall",
            # "geopotential",
            "surface_solar_radiation_downwards",
            "surface_thermal_radiation_downwards",
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
            "surface_pressure",
            "total_precipitation"
        ],
        "year":"2013",
        "month": month,
        "day": [
            "01", "02", "03",
            "04", "05", "06",
            "07", "08", "09",
            "10", "11", "12",
            "13", "14", "15",
            "16", "17", "18",
            "19", "20", "21",
            "22", "23", "24",
            "25", "26", "27",
            "28", "29", "30",
            "31"
        ],
        "time": [
            "00:00", "01:00", "02:00",
            "03:00", "04:00", "05:00",
            "06:00", "07:00", "08:00",
            "09:00", "10:00", "11:00",
            "12:00", "13:00", "14:00",
            "15:00", "16:00", "17:00",
            "18:00", "19:00", "20:00",
            "21:00", "22:00", "23:00"
        ],
        "data_format": "netcdf",
        "download_format": "zip",
        "area": [44, -9.6, 35.7, 4.6] #spanish mainland + balearic islands
        # canary islands --> "area": [29.6, -18.4, 27.5, -13.2]
    }

    client = cdsapi.Client(progress=True)
    client.retrieve(dataset, request, target=f"era5_land_mainland_2013_{month}_2.zip") #end file name with _1.zip for first feature set
