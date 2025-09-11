DEFINE TABLE city SCHEMAFULL;
DEFINE FIELD name ON city TYPE string;
DEFINE FIELD location ON city TYPE point;

FOR $city IN [{"geoname_id": "5881639", "name": "100 Mile House", "ascii_name": "100 Mile House", "feature_class": "P", "feature_code": "PPL", "country_code": "CA", "cou_name_en": "Canada", "country_code_2": null, "admin1_code": "02", "admin2_code": "5941", "admin3_code": "5941005", "admin4_code": null, "population": 1980, "elevation": null, "dem": 928, "timezone": "America/Vancouver", "modification_date": "2019-11-26", "label_en": "Canada", "coordinates": {"lon": -121.28594, "lat": 51.64982}},{"geoname_id": "5896969", "name": "Beaverlodge", "ascii_name": "Beaverlodge", "feature_class": "P", "feature_code": "PPL", "country_code": "CA", "cou_name_en": "Canada", "country_code_2": null, "admin1_code": "01", "admin2_code": "4819009", "admin3_code": null, "admin4_code": null, "population": 2219, "elevation": null, "dem": 723, "timezone": "America/Edmonton", "modification_date": "2024-02-28", "label_en": "Canada", "coordinates": {"lon": -119.43605, "lat": 55.21664}},{"geoname_id": "5911606", "name": "Burnaby", "ascii_name": "Burnaby", "feature_class": "P", "feature_code": "PPLA3", "country_code": "CA", "cou_name_en": "Canada", "country_code_2": null, "admin1_code": "02", "admin2_code": "5915", "admin3_code": "5915025", "admin4_code": null, "population": 202799, "elevation": null, "dem": 87, "timezone": "America/Vancouver", "modification_date": "2019-02-26", "label_en": "Canada", "coordinates": {"lon": -122.95263, "lat": 49.26636}},{"geoname_id": "5920996", "name": "Chertsey", "ascii_name": "Chertsey", "feature_class": "P", "feature_code": "PPL", "country_code": "CA", "cou_name_en": "Canada", "country_code_2": null, "admin1_code": "10", "admin2_code": "14", "admin3_code": "62047", "admin4_code": null, "population": 4836, "elevation": null, "dem": 251, "timezone": "America/Toronto", "modification_date": "2016-06-22", "label_en": "Canada", "coordinates": {"lon": -73.89095, "lat": 46.07109}},{"geoname_id": "5941905", "name": "Dorset Park", "ascii_name": "Dorset Park", "alternate_names": null, "feature_class": "P", "feature_code": "PPLX", "country_code": "CA", "cou_name_en": "Canada", "country_code_2": null, "admin1_code": "08", "admin2_code": "3520", "admin3_code": null, "admin4_code": null, "population": 25003, "elevation": null, "dem": 164, "timezone": "America/Toronto", "modification_date": "2020-05-02", "label_en": "Canada", "coordinates": {"lon": -79.28215, "lat": 43.75386}}]

{
    CREATE type::thing("city", <int>$city.geoname_id) SET
		location = <point>[$city.coordinates.lon, $city.coordinates.lat],
		name = $city.name;
};

FOR $city IN SELECT * FROM city {
    LET $this_location = $city.location;
    LET $closest =
		(SELECT id, location, geo::distance($this_location, location) AS distance FROM city
	ORDER BY distance ASC
	LIMIT 3
		).filter(|$c| $c.distance != 0);
    FOR $closest IN $closest {
      RELATE $city->close_to->$closest SET
	  	distance = geo::distance($city.location, $closest.location);
    };
};

SELECT name, id, ->close_to->city AS neighbours FROM city;
