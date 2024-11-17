var map;
var directionsService;
var directionsRenderer;
var autocompleteStart;
var autocompleteEnd;
var placesService;
var waypoints = [];
var markers = []; // Array to store markers
var passMarkers = [];

function myMap() {
    var mapProp = {
        center: new google.maps.LatLng(39.8283, -98.5795),
        zoom: 2,
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
        resetMap(); // Clear previous markers and route when new location is entered
    });

    google.maps.event.addListener(autocompleteEnd, 'place_changed', function() {
        var place = autocompleteEnd.getPlace();
        if (!place.geometry) {
            console.log("No details available for input: " + place.name);
            return;
        }
        resetMap(); // Clear previous markers and route when new location is entered
    });
}

function handleButtonClick() {
    // Call both functions when the button is clicked
    resetMap();
    calculateRoute();
    var map = document.getElementById("googleMap");
    map.style.width = "600px";
    map.style.height = "600px";         
    scrollToElement('googleMap');   
    

}

function scrollToElement(elementId) {
    // Get the element you want to scroll to
    var element = document.getElementById(elementId);
    if (element) {
        // Scroll the page to that element
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function resetMap() {
    // Clear all previous markers
    markers.forEach(function(marker) {
        marker.setMap(null); // Remove marker from the map
    });
    markers = []; // Reset markers array
    passMarkers = [];

    // Clear the waypoints
    waypoints = [];

    // Clear the previous route
    directionsRenderer.setDirections({routes: []});
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
            var range = document.getElementById("range").value;
            placeMarkersAtIntervals(path, range, map);
        } else {
            alert("Could not calculate route: " + status);
        }
    });
}

function recalculateRoute() {
    var start = document.getElementById("start").value;
    var end = document.getElementById("end").value;

    var request = {
        origin: start,
        destination: end,
        waypoints: waypoints,
        travelMode: google.maps.TravelMode.DRIVING,
    };

    directionsService.route(request, function(result, status) {
        if (status == google.maps.DirectionsStatus.OK) {
            directionsRenderer.setDirections(result);
            // After the route is rendered, generate the export link
            generateExportLink(start, end);
        } else {
            alert("Could not calculate route: " + status);
        }
    });
}

function generateExportLink(start, end) {
    // Generate the URL for Google Maps with waypoints
    var waypointsStr = waypoints.map(function(waypoint) {
        return waypoint.location.lat() + "," + waypoint.location.lng();
    }).join("|");

    // Construct the Google Maps URL with the origin, destination, and waypoints
    var url = "https://www.google.com/maps/dir/?api=1&origin=" + encodeURIComponent(start) + "&destination=" + encodeURIComponent(end) + "&waypoints=" + encodeURIComponent(waypointsStr);

    // Display the link
    console.log("Export URL: " + url);
    document.getElementById('exportLink').innerHTML = "<a href='" + url + "' target='_blank' class='google-maps-link'> ->Open Route in Google Maps <- </a>";

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

            // Search for nearby gas stations or charging stations
            var fuel = document.getElementById("fuelType").value;
            
            const lat = markerLatLng.lat();  // Returns the latitude
            const lng = markerLatLng.lng();  // Returns the longitude

            const coords = {lat,lng};

            if(fuel == "gas_station"){
                searchNearbyPlaces(markerLatLng, map, fuel, coords);
            }
             // types we would implement based on input 'gas_station', 'charging_station', etc.
            
            passMarkers.push(coords);

            markerCount++;
        }
    }

    if(fuel == "electric_vehicle_charging_station"){

        searchChargers(passMarkers,map);

    }

}

function searchChargers(markerarray,map){

        console.log(markerarray);

}

function searchNearbyPlaces(location, map, locationtype, coords) {
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

            // Limit to the first result (the closest one)
            const closestStation = results[0];

            if (closestStation) {
                // Add the closest station as a waypoint in the route
                const waypoint = {
                    location: closestStation.geometry.location,
                    stopover: true,  // Mark as a stopover (waypoint) in the route
                };
                waypoints.push(waypoint); // Add the waypoint to the global waypoints array

                // Create a marker for the gas station on the map
                const marker = new google.maps.Marker({
                    position: closestStation.geometry.location,
                    map: map,
                    title: closestStation.name,
                });

                // Store the marker for later removal
                markers.push(marker);
            }
        } else {
            console.log('Places search failed due to: ' + status);
        }

        recalculateRoute(); // Recalculate route after adding all waypoints
    });
}
