var map;
var directionsService;
var directionsRenderer;
var autocompleteStart;
var autocompleteEnd;
var placesService;

function myMap() {
    var mapProp = {
        center: new google.maps.LatLng(39.8283, -98.5795),
        zoom: 5.5,
    };
    map = new google.maps.Map(document.getElementById("googleMap"), mapProp);

    // Initialize the Directions Service and Renderer
    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer();
    directionsRenderer.setMap(map);

    // Initialize Places Service
    placesService = new google.maps.places.PlacesService(map);

    // Set autocomplete for start and end inputs
    autocompleteStart = new google.maps.places.Autocomplete(document.getElementById('start'));
    autocompleteEnd = new google.maps.places.Autocomplete(document.getElementById('end'));

    // Set autocomplete to places with geographic locations 
    autocompleteStart.setFields(['address_components', 'geometry']);
    autocompleteEnd.setFields(['address_components', 'geometry']);

    // Listener for when a new place is selected
    google.maps.event.addListener(autocompleteStart, 'place_changed', function() {
        var place = autocompleteStart.getPlace();
        if (!place.geometry) {
            console.log("No details available for input: " + place.name);
            return;
        }
    });

    google.maps.event.addListener(autocompleteEnd, 'place_changed', function() {
        var place = autocompleteEnd.getPlace();
        if (!place.geometry) {
            console.log("No details available for input: " + place.name);
            return;
        }
    });
}

function calculateRoute() {
    var start = document.getElementById("start").value;
    var end = document.getElementById("end").value;

    var request = {
        origin: start,
        destination: end,
        travelMode: google.maps.TravelMode.DRIVING,
    };

    directionsService.route(request, function(result, status) {
        if (status == google.maps.DirectionsStatus.OK) {
            directionsRenderer.setDirections(result);

            const path = result.routes[0].overview_path;

            // Place markers every 40 miles along the route
            placeMarkersAtIntervals(path, 150, map);
        } else {
            alert("Could not calculate route: " + status);
        }
    });
}

function placeMarkersAtIntervals(path, markerIntervalMiles, map) {
    const mileInMeters = 1609.34;
    const markerIntervalMeters = markerIntervalMiles * mileInMeters;

    let distanceTraveled = 0;
    let markerCount = 0;

    // Iterate through the polyline path
    for (let i = 0; i < path.length - 1; i++) {
        const startLatLng = path[i];
        const endLatLng = path[i + 1];

        const segmentDistance = google.maps.geometry.spherical.computeDistanceBetween(startLatLng, endLatLng);
        distanceTraveled += segmentDistance;

        while (distanceTraveled >= (markerCount + 1) * markerIntervalMeters) {
            const fraction = (markerCount + 1) * markerIntervalMeters / distanceTraveled;
            const markerLatLng = google.maps.geometry.spherical.interpolate(startLatLng, endLatLng, fraction);

            // Place the marker at the calculated position
            const marker = new google.maps.Marker({
                position: markerLatLng,
                map: map,
                title: `Marker at ${(markerCount + 1) * markerIntervalMiles} miles`,
            });

            // Search for nearby gas stations or charging stations
            searchNearbyPlaces(markerLatLng, map, 'charging_station'); // types we would implement based on input 'gas_station', 'charging_station', 'restaurant', 'supermarket'

            markerCount++;
        }
    }
}

function searchNearbyPlaces(location, ma, locationtype) {
    const request = {
        location: location,
        radius: 20000, // Search within a 20km radius
        type: [locationtype], // Search for gas stations and charging stations
    };

    placesService.nearbySearch(request, function(results, status) {
        if (status === google.maps.places.PlacesServiceStatus.OK) {
            // Sort results by distance (closest first)
            results.sort(function(a, b) {
                return google.maps.geometry.spherical.computeDistanceBetween(location, a.geometry.location) -
                    google.maps.geometry.spherical.computeDistanceBetween(location, b.geometry.location);
            });

            // Limit to the first 2 results (the closest ones)
            results.slice(0, 2).forEach(function(place) {
                new google.maps.Marker({
                    position: place.geometry.location,
                    map: map,
                    title: place.name,
                });
            });
        } else {
            console.log('Places search failed due to: ' + status);
        }
    });
}
