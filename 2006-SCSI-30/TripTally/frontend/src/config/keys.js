import Constants from 'expo-constants';
// Read Google Maps API key from environment/build config. Do NOT store real keys in source.
// In development, set GOOGLE_MAPS_API_KEY in your local environment or use app.json configuration.
export const GOOGLE_MAPS_APIKEY = process.env.GOOGLE_MAPS_API_KEY || (Constants.expoConfig?.ios?.config?.googleMapsApiKey) || 'REPLACE_WITH_GOOGLE_MAPS_API_KEY';

// Update this to your computer's IP address (run 'ipconfig' in PowerShell to find it)
// Make sure your phone and computer are on the SAME WiFi network
export const BASE_URL = "http:/192.168.50.250:8000";
