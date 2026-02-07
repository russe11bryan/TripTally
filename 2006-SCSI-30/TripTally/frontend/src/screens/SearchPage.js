// src/screens/SearchPage.js
import React, { useRef, useState, useEffect } from "react";
import {
 View,
 Text,
 TextInput,
 TouchableOpacity,
 FlatList,
 ActivityIndicator,
 Keyboard,
 Platform,
 Alert,
 Image, // thumbnails
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as Location from "expo-location";
import Ionicons from "@expo/vector-icons/Ionicons";
import useThemedStyles from "../hooks/useThemedStyles";
import { BASE_URL } from "../config/keys"; // make sure this exists
import { useAuth } from "../context/AuthContext";


/* ---------- Backend base URL ---------- */
const DEV_ANDROID = "http://10.0.2.2:8080";
const DEV_IOS = "http://localhost:8080";
const DEV_DEVICE = "http://192.168.10.131:8080"; // your LAN/ngrok when testing on a real phone
const USE_DEVICE = true; // set false if using emulators only


const API_BASE =
 BASE_URL ||
 (__DEV__
   ? USE_DEVICE
     ? DEV_DEVICE
     : Platform.OS === "android"
     ? DEV_ANDROID
     : DEV_IOS
   : "https://your-prod-domain.com");
/* ------------------------------------- */


// Build photo URL from backend /maps/photos
function getPhotoUrl(photoRef, maxwidth = 120) {
 if (!photoRef) return null;
 return `${API_BASE}/maps/photos?photo_reference=${encodeURIComponent(
   photoRef
 )}&maxwidth=${maxwidth}`;
}


const newSessionToken = () =>
 Math.random().toString(36).slice(2) + Date.now().toString(36);


// Validation constants
const MAX_SEARCH_LENGTH = 200;
const MIN_SEARCH_LENGTH = 2;

// Validate search input
const validateSearchInput = (text) => {
  // Check if empty or only whitespace
  if (!text || text.trim().length === 0) {
    return { isValid: false, error: null };
  }
  
  // Check minimum length after trimming
  if (text.trim().length < MIN_SEARCH_LENGTH) {
    return { isValid: false, error: `Search must be at least ${MIN_SEARCH_LENGTH} characters` };
  }
  
  // Check maximum length
  if (text.length > MAX_SEARCH_LENGTH) {
    return { isValid: false, error: `Search is too long (max ${MAX_SEARCH_LENGTH} characters)` };
  }
  
  // Check for excessive repeated characters (e.g., "aaaaaaa...")
  const repeatedPattern = /(.)\1{9,}/; // 10+ same characters in a row
  if (repeatedPattern.test(text)) {
    return { isValid: false, error: 'Invalid search pattern' };
  }
  
  return { isValid: true, error: null };
};

export default function SearchPage({ navigation }) {
 const { user } = useAuth();
 const { styles, theme } = useThemedStyles(({ colors }) => ({
   root: { flex: 1, backgroundColor: colors.background, paddingTop: 70 },
   header: {
     flexDirection: "row",
     alignItems: "center",
     paddingHorizontal: 16,
     marginBottom: 10,
   },
   back: { fontSize: 18, color: colors.text },
   inputContainer: {
     flex: 1,
     flexDirection: "row",
     alignItems: "center",
     backgroundColor: colors.card,
     borderRadius: 10,
     marginLeft: 10,
     borderWidth: 1,
     borderColor: colors.border,
     paddingRight: 8,
   },
   input: {
     flex: 1,
     padding: 12,
     color: colors.text,
   },
   row: {
     paddingHorizontal: 16,
     paddingVertical: 12,
     borderBottomColor: colors.border,
     borderBottomWidth: 1,
     flexDirection: "row",
     alignItems: "center",
     justifyContent: "space-between",
   },
   rowTitle: { fontWeight: "700", color: colors.text },
   rowSubtitle: {
     color: colors.muted,
     fontSize: 13,
     marginTop: 2,
   },
   distanceText: {
     fontSize: 12,
     color: colors.muted,
     marginLeft: 4,
     fontWeight: "600",
   },
   sectionHeader: {
     flexDirection: "row",
     justifyContent: "space-between",
     alignItems: "center",
     paddingHorizontal: 16,
     paddingVertical: 12,
     backgroundColor: colors.background,
   },
   sectionTitle: {
     fontSize: 16,
     fontWeight: "600",
     color: colors.text,
   },
   clearButton: {
     padding: 4,
     justifyContent: "center",
     alignItems: "center",
   },
   clearTextButton: {
     fontSize: 14,
     color: colors.accent,
   },
   recentRow: {
     paddingHorizontal: 16,
     paddingVertical: 12,
     borderBottomColor: colors.border,
     borderBottomWidth: 1,
     flexDirection: "row",
     alignItems: "center",
   },
   recentIcon: {
     marginRight: 12,
   },
   recentTextContainer: {
     flex: 1,
   },
   shortcutsContainer: {
     flexDirection: "row",
     paddingHorizontal: 16,
     paddingVertical: 12,
     gap: 12,
   },
   shortcutButton: {
     flex: 1,
     flexDirection: "row",
     alignItems: "center",
     justifyContent: "center",
     backgroundColor: colors.card,
     borderRadius: 12,
     padding: 12,
     borderWidth: 1,
     borderColor: colors.border,
   },
   shortcutIcon: {
     marginRight: 8,
   },
   shortcutText: {
     fontSize: 15,
     fontWeight: "600",
     color: colors.text,
   },
   nearbyButton: {
     marginHorizontal: 16,
     marginVertical: 8,
     backgroundColor: colors.accent,
     borderRadius: 12,
     padding: 16,
     flexDirection: "row",
     alignItems: "center",
     justifyContent: "center",
   },
   nearbyButtonText: {
     color: colors.card,
     fontSize: 16,
     fontWeight: "700",
     marginLeft: 8,
   },
   inputError: {
     color: colors.danger,
     fontSize: 13,
     paddingHorizontal: 16,
     marginTop: 4,
     marginBottom: 8,
   },
   inputContainerError: {
     borderColor: colors.danger,
     borderWidth: 1.5,
   },
   backendError: {
     backgroundColor: colors.danger + '15', // 15 = ~8% opacity
     color: colors.danger,
     fontSize: 13,
     paddingHorizontal: 16,
     paddingVertical: 10,
     marginHorizontal: 16,
     marginTop: 8,
     marginBottom: 8,
     borderRadius: 8,
     borderLeftWidth: 3,
     borderLeftColor: colors.danger,
   },
 }));


 const [query, setQuery] = useState("");
 const [results, setResults] = useState([]); // [{ id, name, place_id, distance, photoUrl? }]
 const [recentSearches, setRecentSearches] = useState([]); // Recent searches
 const [loading, setLoading] = useState(false);
 const [showNearbyOption, setShowNearbyOption] = useState(false);
 const [userLocation, setUserLocation] = useState(null);
 const [inputError, setInputError] = useState('');
 const [backendError, setBackendError] = useState('');


 const debounceRef = useRef(null);
 const sessionRef = useRef(newSessionToken());


 // Common place types for nearby search with aliases
 const PLACE_TYPE_MAPPINGS = {
   restaurant: ["restaurant", "restaurants", "food", "dining", "eat"],
   cafe: ["cafe", "cafes", "coffee", "coffee shop"],
   grocery: ["grocery", "groceries", "supermarket", "market"],
   pharmacy: ["pharmacy", "pharmacies", "drugstore", "chemist"],
   hospital: ["hospital", "hospitals", "medical", "clinic"],
   gas_station: ["gas station", "gas", "fuel", "petrol"],
   atm: ["atm", "cash", "money"],
   bank: ["bank", "banks", "banking"],
   park: ["park", "parks", "playground"],
   gym: ["gym", "gyms", "fitness", "workout"],
   library: ["library", "libraries"],
   shopping_mall: ["mall", "shopping mall", "shopping center", "shopping"],
   parking: ["parking", "car park", "parking lot"],
   bar: ["bar", "bars", "pub", "nightlife"],
   movie_theater: ["movie", "movies", "cinema", "theater"],
   store: ["store", "stores", "shop", "shops"],
 };


 // Load recent searches on mount
 useEffect(() => {
   loadRecentSearches();
   getUserLocation();
 }, [user?.id]);


 // Recalculate distances when user location is updated
 useEffect(() => {
   if (userLocation) loadRecentSearches();
 }, [userLocation]);


 useEffect(() => () => clearTimeout(debounceRef.current), []);


 // Get user's current location
 const getUserLocation = async () => {
   try {
     const { status } = await Location.requestForegroundPermissionsAsync();
     if (status === "granted") {
       const location = await Location.getCurrentPositionAsync({});
       setUserLocation({
         latitude: location.coords.latitude,
         longitude: location.coords.longitude,
       });
     }
   } catch (error) {
     console.error("Error getting user location:", error);
   }
 };


 // Haversine (km)
 const calculateDistance = (lat1, lon1, lat2, lon2) => {
   const R = 6371;
   const dLat = ((lat2 - lat1) * Math.PI) / 180;
   const dLon = ((lon2 - lon1) * Math.PI) / 180;
   const a =
     Math.sin(dLat / 2) * Math.sin(dLat / 2) +
     Math.cos((lat1 * Math.PI) / 180) *
       Math.cos((lat2 * Math.PI) / 180) *
       Math.sin(dLon / 2) *
       Math.sin(dLon / 2);
   const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
   return R * c;
 };


 const formatDistance = (distanceKm) => {
   if (distanceKm < 1) return `${Math.round(distanceKm * 1000)}m`;
   return `${distanceKm.toFixed(1)}km`;
 };


 // Load recent searches from AsyncStorage
 const loadRecentSearches = async () => {
   if (!user?.id) return;
   try {
     const key = `recent_searches_${user.id}`;
     const stored = await AsyncStorage.getItem(key);
     if (stored) {
       let searches = JSON.parse(stored);
       if (userLocation) {
         searches = searches.map((search) => {
           if (search.latitude && search.longitude) {
             const distance = calculateDistance(
               userLocation.latitude,
               userLocation.longitude,
               search.latitude,
               search.longitude
             );
             return { ...search, distance };
           }
           return { ...search, distance: null };
         });
       }
       setRecentSearches(searches);
     }
   } catch (error) {
     console.error("Error loading recent searches:", error);
   }
 };


 // Find matching place type from query
 const findMatchingPlaceType = (q) => {
   const lowerQuery = q.toLowerCase().trim();
   for (const [type, aliases] of Object.entries(PLACE_TYPE_MAPPINGS)) {
     for (const alias of aliases) {
       if (lowerQuery === alias) return type;
       const regex = new RegExp(`\\b${alias}\\b`, "i");
       if (regex.test(lowerQuery)) return type;
     }
   }
   return null;
 };


 // Save a search
 const saveRecentSearch = async (place) => {
   if (!user?.id) return;
   try {
     const key = `recent_searches_${user.id}`;
     const newSearch = {
       id: place.placeId || place.name,
       name: place.name,
       address: place.address || null,
       place_id: place.placeId,
       latitude: place.latitude,
       longitude: place.longitude,
       timestamp: Date.now(),
     };
     const filtered = recentSearches.filter((s) => s.id !== newSearch.id);
     const updated = [newSearch, ...filtered].slice(0, 10);
     await AsyncStorage.setItem(key, JSON.stringify(updated));
     setRecentSearches(updated);
   } catch (error) {
     console.error("Error saving recent search:", error);
   }
 };


 const clearRecentSearches = async () => {
   if (!user?.id) return;
   try {
     const key = `recent_searches_${user.id}`;
     await AsyncStorage.removeItem(key);
     setRecentSearches([]);
   } catch (error) {
     console.error("Error clearing recent searches:", error);
   }
 };


 // ----- Debounced search handler -----
 const handleSearch = (text) => {
   setQuery(text);
   clearTimeout(debounceRef.current);


   if (!text || text.length < 2) {
     setResults([]);
     setShowNearbyOption(false);
     setBackendError('');
     return;
   }


   setShowNearbyOption(true);


   debounceRef.current = setTimeout(async () => {
     setLoading(true);
     setBackendError(''); // Clear backend error before new search
     try {
       let list = [];


       // 1) Nearby Search (if we have user location) — ranked by distance
       if (userLocation) {
         try {
           const nearbyUrl = `${API_BASE}/maps/nearby?location=${userLocation.latitude},${userLocation.longitude}&radius=10000&keyword=${encodeURIComponent(
             text
           )}&rankby=distance`;
           const nearbyRes = await fetch(nearbyUrl);
           
           // Handle HTTP errors
           if (!nearbyRes.ok) {
             if (nearbyRes.status === 429) {
               setBackendError('⚠️ Too many requests. Please wait a moment and try again.');
             } else if (nearbyRes.status >= 500) {
               setBackendError(`❌ Server error (${nearbyRes.status}). Please try again later.`);
             } else if (nearbyRes.status === 404) {
               setBackendError('❌ Search service not found (404).');
             } else {
               setBackendError(`❌ Request failed (${nearbyRes.status}). Please try again.`);
             }
             return;
           }
           
           if (nearbyRes.ok) {
             const nearbyData = await nearbyRes.json();
             const arr = Array.isArray(nearbyData?.results)
               ? nearbyData.results
               : nearbyData?.routes || [];
             if (nearbyData.status === "OK" && arr.length > 0) {
               list = arr.map((place) => {
                 const distance = calculateDistance(
                   userLocation.latitude,
                   userLocation.longitude,
                   place.lat,
                   place.lng
                 );
                 const photoRef = place?.photo?.photo_reference;
                 const photoUrl = photoRef ? getPhotoUrl(photoRef, 120) : null;
                 return {
                   id: place.place_id || place.name,
                   name: place.name,
                   address: place.address || null,
                   place_id: place.place_id,
                   distance,
                   lat: place.lat,
                   lng: place.lng,
                   photoUrl,
                 };
               });
             }
           }
         } catch (nearbyError) {
           console.error("Nearby search error:", nearbyError);
           setBackendError(`❌ Network error: ${nearbyError.message}`);
         }
       }


       // 2) Autocomplete: fetch BOTH biased and global, then merge & de-dupe
       const fetchPredictions = async (url) => {
         const res = await fetch(url);
         if (!res.ok) {
           if (res.status === 429) {
             setBackendError('⚠️ Too many requests (429). Please wait a moment.');
             return [];
           }
           if (res.status >= 500) {
             setBackendError(`❌ Server error (${res.status}). Please try again later.`);
             return [];
           }
           if (res.status === 422) {
             setBackendError('❌ Invalid request format (422).');
             return [];
           }
           setBackendError(`❌ Request failed (${res.status}).`);
           throw new Error(`HTTP ${res.status}`);
         }
         const data = await res.json();
         return (data?.predictions || []).map((p) => ({
           id: p.place_id || p.description,
           name: p.description,
           place_id: p.place_id,
         }));
       };


       const baseQS = `input=${encodeURIComponent(text)}&sessiontoken=${encodeURIComponent(
         sessionRef.current
       )}`;
       const biasedQS = userLocation
         ? `${baseQS}&location=${userLocation.latitude},${userLocation.longitude}&radius=10000`
         : baseQS;


       const urlBiased = `${API_BASE}/maps/places-autocomplete?${biasedQS}`;
       const urlGlobal = `${API_BASE}/maps/places-autocomplete?${baseQS}`;


       const [biasedPreds, globalPreds] = await Promise.all([
         fetchPredictions(urlBiased),
         fetchPredictions(urlGlobal),
       ]);


       // merge + de-dupe by place_id (or name fallback)
       const seen = new Set();
       const mergedPreds = [...biasedPreds, ...globalPreds].filter((it) => {
         const key = it.place_id || it.name;
         if (seen.has(key)) return false;
         seen.add(key);
         return true;
       });


       // Enrich predictions with coords + distance + small photo (if we have location)
       let enrichedPreds = mergedPreds;
       if (userLocation && mergedPreds.length > 0) {
         enrichedPreds = await Promise.all(
           mergedPreds.map(async (item) => {
             try {
               if (!item.place_id)
                 return { ...item, distance: null, photoUrl: null };
               const detailsUrl = `${API_BASE}/maps/place-details?place_id=${encodeURIComponent(
                 item.place_id
               )}`; // backend returns geometry + photos
               const detailsRes = await fetch(detailsUrl);
               if (!detailsRes.ok)
                 return { ...item, distance: null, photoUrl: null };
               const detailsData = await detailsRes.json();


               const lat =
                 detailsData?.lat ??
                 detailsData?.result?.geometry?.location?.lat;
               const lng =
                 detailsData?.lng ??
                 detailsData?.result?.geometry?.location?.lng;


               const photoRef =
                 detailsData?.photos?.[0]?.photo_reference ?? null;
               const photoUrl = photoRef ? getPhotoUrl(photoRef, 120) : null;


               if (lat && lng) {
                 const distance = calculateDistance(
                   userLocation.latitude,
                   userLocation.longitude,
                   lat,
                   lng
                 );
                 return { ...item, distance, lat, lng, photoUrl };
               }
               return { ...item, distance: null, photoUrl };
             } catch (e) {
               return { ...item, distance: null, photoUrl: null };
             }
           })
         );


         // sort by distance if available
         enrichedPreds.sort((a, b) => {
           if (a.distance == null && b.distance == null) return 0;
           if (a.distance == null) return 1;
           if (b.distance == null) return -1;
           return a.distance - b.distance;
         });
       }


       // 3) If Nearby list already has results, append any *new* predictions not present
       if (list.length > 0) {
         const existing = new Set(
           list.map((x) => x.place_id || x.id || x.name)
         );
         const toAppend = enrichedPreds.filter((p) => {
           const key = p.place_id || p.id || p.name;
           return !existing.has(key);
         });
         list = [...list, ...toAppend];
       } else {
         list = enrichedPreds;
       }


       setResults(list);
     } catch (err) {
       console.error("Autocomplete error:", err);
       if (!backendError) { // Only set if not already set
         setBackendError(`❌ Search failed: ${err.message}`);
       }
       setResults([]);
     } finally {
       setLoading(false);
     }
   }, 800);
 };


 // ----- Tap a prediction -> fetch coords -> go to Location -----
 const handleSelect = async (item) => {
   Keyboard.dismiss();
   setBackendError(''); // Clear previous errors
   try {
     setLoading(true);


     let lat = null;
     let lng = null;


     if (item.place_id) {
       // Try place-details first (default includes photos)
       const detailsUrl = `${API_BASE}/maps/place-details?place_id=${encodeURIComponent(
         item.place_id
       )}`;
       const res = await fetch(detailsUrl);
       if (!res.ok) {
         if (res.status === 404) {
           setBackendError('❌ Place not found (404).');
         } else if (res.status >= 500) {
           setBackendError(`❌ Server error (${res.status}).`);
         } else if (res.status === 429) {
           setBackendError('⚠️ Too many requests (429). Please wait.');
         } else {
           setBackendError(`❌ Failed to fetch place details (${res.status}).`);
         }
         throw new Error(`HTTP ${res.status}`);
       }
       const data = await res.json();


       lat = data?.lat ?? data?.result?.geometry?.location?.lat ?? null;
       lng = data?.lng ?? data?.result?.geometry?.location?.lng ?? null;
     }


     // Fallback to geocode (and also grab a clean display name)
     if (lat == null || lng == null) {
       const geoUrl = `${API_BASE}/maps/geocode?address=${encodeURIComponent(
         item.name
       )}`;
       const gres = await fetch(geoUrl);
       if (!gres.ok) {
         if (gres.status === 404) {
           setBackendError('❌ Location not found (404).');
         } else if (gres.status >= 500) {
           setBackendError(`❌ Geocoding server error (${gres.status}).`);
         } else if (gres.status === 429) {
           setBackendError('⚠️ Too many geocoding requests (429). Please wait.');
         } else {
           setBackendError(`❌ Geocoding failed (${gres.status}).`);
         }
         throw new Error(`HTTP ${gres.status}`);
       }
       const gdata = await gres.json();
       const first = Array.isArray(gdata?.results) ? gdata.results[0] : null;
       lat = lat ?? first?.lat ?? null;
       lng = lng ?? first?.lng ?? null;
       item.name = first?.formatted_address ?? item.name;
     }


     if (lat == null || lng == null) {
       setBackendError('❌ Could not resolve coordinates for the selected place.');
       throw new Error("Could not resolve coordinates for the selected place.");
     }


     // New user session for the next search flow
     sessionRef.current = newSessionToken();


     // Save to recent searches - use item.name as it contains the full description
     const placeToSave = {
       name: item.name,
       address: item.name, // Store full description as address too
       latitude: lat,
       longitude: lng,
       placeId: item.place_id ?? null,
     };
     await saveRecentSearch(placeToSave);


     // Navigate to Location screen
     navigation.navigate("Location", {
       place: placeToSave,
     });
   } catch (e) {
     console.error("Select place error:", e);
     if (!backendError) { // Only set if not already set
       setBackendError(`❌ Failed to select place: ${e.message}`);
     }
   } finally {
     setLoading(false);
   }
 };


 const submitFirst = () => {
   if (results[0]) handleSelect(results[0]);
 };


 const handleRecentSearchSelect = async (recentItem) => {
   Keyboard.dismiss();
   navigation.navigate("Location", {
     place: {
       name: recentItem.name,
       address: recentItem.address || recentItem.name, // Fallback to name if address not stored
       latitude: recentItem.latitude,
       longitude: recentItem.longitude,
       placeId: recentItem.place_id,
     },
   });
 };


 const handleSearchNearby = () => {
   Keyboard.dismiss();
   
   // Validate before navigating
   const validation = validateSearchInput(query);
   if (!validation.isValid) {
     if (validation.error) {
       setInputError(validation.error);
     }
     return;
   }
   
   const lowerQuery = query.toLowerCase().trim();
   const matchedType = findMatchingPlaceType(lowerQuery);
   navigation.navigate("NearbyPlacesMap", {
     searchQuery: query.trim(),
     placeType: matchedType || null,
   });
 };


 const handleHomePress = () => {
   Keyboard.dismiss();
   if (!user?.home_latitude || !user?.home_longitude) {
     // Navigate directly to SetLocationPage to set home location
     navigation.navigate("SetLocation", { locationType: "home" });
     return;
   }
   navigation.navigate("Directions", {
     destination: {
       latitude: user.home_latitude,
       longitude: user.home_longitude,
       name: user.home_address || "Home",
     },
   });
 };


 const handleWorkPress = () => {
   Keyboard.dismiss();
   if (!user?.work_latitude || !user?.work_longitude) {
     // Navigate directly to SetLocationPage to set work location
     navigation.navigate("SetLocation", { locationType: "work" });
     return;
   }
   navigation.navigate("Directions", {
     destination: {
       latitude: user.work_latitude,
       longitude: user.work_longitude,
       name: user.work_address || "Work",
     },
   });
 };


 return (
   <View style={styles.root}>
     <View className="header" style={styles.header}>
       <TouchableOpacity onPress={() => navigation.goBack()}>
         <Text style={styles.back}>←</Text>
       </TouchableOpacity>
       <View style={[styles.inputContainer, inputError ? styles.inputContainerError : null]}>
         <TextInput
           style={styles.input}
           placeholder="Search destination..."
           placeholderTextColor={theme.colors.muted}
           value={query}
           onChangeText={handleSearch}
           autoCorrect={false}
           autoCapitalize="none"
           returnKeyType="search"
           onSubmitEditing={submitFirst}
           maxLength={MAX_SEARCH_LENGTH}
         />
         {query.length > 0 && (
           <TouchableOpacity
             onPress={() => {
               setQuery("");
               setInputError("");
               setBackendError("");
             }}
             style={styles.clearButton}
           >
             <Ionicons
               name="close-circle"
               size={20}
               color={theme.colors.muted}
             />
           </TouchableOpacity>
         )}
       </View>
     </View>

     {/* Input validation error message */}
     {inputError && (
       <Text style={styles.inputError}>{inputError}</Text>
     )}

     {/* Backend HTTP error message */}
     {backendError && (
       <Text style={styles.backendError}>{backendError}</Text>
     )}


     {/* Home and Work Shortcuts - Only show when not searching */}
     {query.length === 0 && (
       <View style={styles.shortcutsContainer}>
         <TouchableOpacity
           style={styles.shortcutButton}
           onPress={handleHomePress}
         >
           <Ionicons
             name="home"
             size={20}
             color={theme.colors.accent}
             style={styles.shortcutIcon}
           />
           <Text style={styles.shortcutText}>Home</Text>
         </TouchableOpacity>


         <TouchableOpacity
           style={styles.shortcutButton}
           onPress={handleWorkPress}
         >
           <Ionicons
             name="briefcase"
             size={20}
             color={theme.colors.accent}
             style={styles.shortcutIcon}
           />
           <Text style={styles.shortcutText}>Work</Text>
         </TouchableOpacity>
       </View>
     )}


     {loading && (
       <ActivityIndicator
         size="small"
         color={theme.colors.accent}
         style={{ marginVertical: 10 }}
       />
     )}


     {/* Show "Search Nearby" button for any search query */}
     {showNearbyOption && query.length > 0 && (
       <TouchableOpacity style={styles.nearbyButton} onPress={handleSearchNearby}>
         <Ionicons name="map" size={20} color={theme.colors.card} />
         <Text style={styles.nearbyButtonText}>Search nearby "{query}"</Text>
       </TouchableOpacity>
     )}


     {/* Recent searches */}
     {query.length === 0 && recentSearches.length > 0 && (
       <>
         <View style={styles.sectionHeader}>
           <Text style={styles.sectionTitle}>Recent Searches</Text>
           <TouchableOpacity onPress={clearRecentSearches}>
             <Text style={styles.clearTextButton}>Clear</Text>
           </TouchableOpacity>
         </View>
         <FlatList
           data={recentSearches}
           keyExtractor={(item) => String(item.id)}
           keyboardShouldPersistTaps="handled"
           renderItem={({ item }) => (
             <TouchableOpacity
               style={styles.recentRow}
               onPress={() => handleRecentSearchSelect(item)}
             >
               <Ionicons
                 name="time-outline"
                 size={20}
                 color={theme.colors.muted}
                 style={styles.recentIcon}
               />
               <View style={styles.recentTextContainer}>
                 <Text style={styles.rowTitle}>{item.name}</Text>
                 {item.address && (
                   <Text style={styles.rowSubtitle} numberOfLines={1}>
                     {item.address}
                   </Text>
                 )}
                 {item.distance !== null &&
                   item.distance !== undefined && (
                     <View
                       style={{
                         flexDirection: "row",
                         alignItems: "center",
                         marginTop: 4,
                       }}
                     >
                       <Ionicons
                         name="walk"
                         size={14}
                         color={theme.colors.muted}
                       />
                       <Text style={styles.distanceText}>
                         {formatDistance(item.distance)}
                       </Text>
                     </View>
                   )}
               </View>
               <Ionicons
                 name="arrow-forward"
                 size={18}
                 color={theme.colors.muted}
               />
             </TouchableOpacity>
           )}
         />
       </>
     )}


     {/* Search results */}
     {query.length > 0 && (
       <FlatList
         data={results}
         keyExtractor={(item) => String(item.id)}
         keyboardShouldPersistTaps="handled"
         renderItem={({ item }) => (
           <TouchableOpacity
             style={styles.row}
             onPress={() => handleSelect(item)}
           >
             <View style={{ flex: 1, paddingRight: 12 }}>
               {/* small thumbnail if available */}
               {item.photoUrl && (
                 <Image
                   source={{ uri: item.photoUrl }}
                   style={{
                     width: 64,
                     height: 64,
                     borderRadius: 8,
                     marginBottom: 6,
                     backgroundColor: "#eee",
                   }}
                 />
               )}
               <Text style={styles.rowTitle}>{item.name}</Text>
               {item.address && (
                 <Text style={styles.rowSubtitle} numberOfLines={1}>
                   {item.address}
                 </Text>
               )}
               {item.distance !== null &&
                 item.distance !== undefined && (
                   <View
                     style={{
                       flexDirection: "row",
                       alignItems: "center",
                       marginTop: 4,
                     }}
                   >
                     <Ionicons
                       name="walk"
                       size={14}
                       color={theme.colors.muted}
                     />
                     <Text style={styles.distanceText}>
                       {formatDistance(item.distance)}
                     </Text>
                   </View>
                 )}
             </View>
             <Ionicons name="arrow-forward" size={18} color={theme.colors.muted} />
           </TouchableOpacity>
         )}
         ListEmptyComponent={
           !loading && query.length > 2 ? (
             <Text
               style={{
                 textAlign: "center",
                 color: theme.colors.muted,
                 marginTop: 20,
               }}
             >
               No results found
             </Text>
           ) : null
         }
       />
     )}
   </View>
 );
}





