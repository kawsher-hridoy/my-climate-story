import { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Tooltip,
  useMap,
  useMapEvents,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { Place } from "../lib/types";
import { useLocale } from "./shared";

function MapEvents({
  onSelect,
}: {
  onSelect: (latitude: number, longitude: number) => void;
}) {
  useMapEvents({
    click: (event) =>
      onSelect(
        Number(event.latlng.lat.toFixed(4)),
        Number(event.latlng.lng.toFixed(4)),
      ),
  });
  return null;
}
function Focus({
  latitude,
  longitude,
}: {
  latitude: number;
  longitude: number;
}) {
  const map = useMap();
  useEffect(() => {
    map.flyTo(
      [Math.max(-85.05, Math.min(85.05, latitude)), longitude],
      Math.max(map.getZoom(), 7),
      { duration: 0.6 },
    );
  }, [latitude, longitude, map]);
  return null;
}
export default function ExplorerMap({
  places,
  selected,
  onSelect,
  onPlace,
  layer,
  date,
  onTileError,
}: {
  places: Place[];
  selected: { latitude: number; longitude: number } | null;
  onSelect: (latitude: number, longitude: number) => void;
  onPlace: (place: Place) => void;
  layer: string;
  date: string;
  onTileError: () => void;
}) {
  const locale = useLocale();
  const url =
    layer === "satellite"
      ? `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/${date}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpeg`
      : "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
  return (
    <MapContainer
      center={[23.8, 90.4]}
      zoom={7}
      scrollWheelZoom={false}
      className="explorer-map"
      aria-label={
        locale === "bn"
          ? "জায়গা নির্বাচনের মানচিত্র"
          : "Map for selecting a place"
      }
    >
      <TileLayer
        key={`${layer}-${date}`}
        url={url}
        attribution={
          layer === "satellite"
            ? "NASA GIBS / MODIS"
            : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }
        maxNativeZoom={layer === "satellite" ? 9 : 19}
        maxZoom={19}
        eventHandlers={{ tileerror: onTileError }}
      />
      <MapEvents onSelect={onSelect} />
      {places.map((place) => (
        <CircleMarker
          key={place.id}
          bubblingMouseEvents={false}
          center={[place.coordinates.latitude, place.coordinates.longitude]}
          radius={7}
          pathOptions={{
            color: "#fff",
            weight: 2,
            fillColor: "#1b654f",
            fillOpacity: 1,
          }}
          eventHandlers={{
            click: (event) => {
              event.originalEvent.stopPropagation();
              onPlace(place);
            },
          }}
        >
          <Tooltip>{place.name[locale]}</Tooltip>
        </CircleMarker>
      ))}
      {selected && (
        <>
          <Focus {...selected} />
          <CircleMarker
            center={[
              Math.max(-85.05, Math.min(85.05, selected.latitude)),
              selected.longitude,
            ]}
            radius={11}
            pathOptions={{
              color: "#fff",
              weight: 3,
              fillColor: "#b76740",
              fillOpacity: 1,
            }}
          />
        </>
      )}
    </MapContainer>
  );
}
