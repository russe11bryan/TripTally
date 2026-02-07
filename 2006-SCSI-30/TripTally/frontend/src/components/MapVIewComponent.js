// src/components/MapViewComponent.js
import React from 'react';
import MapView, { Marker, Polyline } from 'react-native-maps';

export default function MapViewComponent({ routePoints = [], markers = [] }) {
  const defaultRegion = {
    latitude: 1.3483,
    longitude: 103.6831,
    latitudeDelta: 0.01,
    longitudeDelta: 0.01,
  };

  return (
    <MapView
      style={{ flex: 1 }}
      initialRegion={defaultRegion}
      showsUserLocation
      followsUserLocation
    >
      {markers.map((m, i) => (
        <Marker key={i} coordinate={m.coords} title={m.title} />
      ))}

      {routePoints.length > 1 && (
        <Polyline
          coordinates={routePoints}
          strokeColor="#2f7cf6"
          strokeWidth={5}
        />
      )}
    </MapView>
  );
}
