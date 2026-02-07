import React, { useMemo, useState, useEffect, useCallback } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator, RefreshControl, Alert, TextInput, Modal, ScrollView, SafeAreaView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import MapView, { Marker, Polyline, PROVIDER_GOOGLE } from 'react-native-maps';
import { useFocusEffect } from '@react-navigation/native';
import Card from '../components/Card';
import HeaderBackButton from '../components/HeaderBackButton';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { apiGet, apiPost } from '../services/api';

export default function UserSuggestedRoutePage({ navigation }) {
  const { theme } = useTheme();
  const { user } = useAuth();
  const styles = useMemo(() => createStyles(theme), [theme]);
  
  const [routes, setRoutes] = useState([]);
  const [filteredRoutes, setFilteredRoutes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [likingIds, setLikingIds] = useState(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [modalRegion, setModalRegion] = useState(null);
  const modalMapRef = React.useRef(null);

  const fetchRoutes = async (isRefresh = false) => {
    try {
      if (!isRefresh) setLoading(true);
      
      const userId = user?.id;
      const url = userId ? `/user-routes?user_id=${userId}` : '/user-routes';
      const data = await apiGet(url);
      
      console.log('Fetched user routes:', data.length);
      
      // Sort by likes (highest first), then by created_at (newest first)
      const sorted = data.sort((a, b) => {
        if (b.likes !== a.likes) {
          return b.likes - a.likes;
        }
        return new Date(b.created_at) - new Date(a.created_at);
      });
      
      setRoutes(sorted);
      setFilteredRoutes(sorted);
    } catch (error) {
      console.error('Error fetching routes:', error);
      Alert.alert('Error', 'Failed to load routes. Please try again.');
    } finally {
      setLoading(false);
      if (isRefresh) setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchRoutes();
  }, [user?.id]);

  useFocusEffect(
    useCallback(() => {
      console.log('UserSuggestedRoutePage focused - refreshing data');
      fetchRoutes();
    }, [user?.id])
  );

  useEffect(() => {
    // Filter routes based on search query
    if (searchQuery.trim() === '') {
      setFilteredRoutes(routes);
    } else {
      const query = searchQuery.toLowerCase();
      const filtered = routes.filter(route =>
        route.title.toLowerCase().includes(query) ||
        route.description.toLowerCase().includes(query) ||
        route.transport_mode.toLowerCase().includes(query) ||
        (route.created_by && route.created_by.toLowerCase().includes(query))
      );
      setFilteredRoutes(filtered);
    }
  }, [searchQuery, routes]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchRoutes(true);
  };

  const handleLike = async (route) => {
    if (!user?.id) {
      Alert.alert('Login Required', 'Please log in to like routes.');
      return;
    }

    if (likingIds.has(route.id)) return;

    const isCurrentlyLiked = route.is_liked_by_user;

    // Optimistic update
    setRoutes(prev =>
      prev.map(r =>
        r.id === route.id
          ? { 
              ...r, 
              likes: isCurrentlyLiked ? r.likes - 1 : r.likes + 1,
              is_liked_by_user: !isCurrentlyLiked
            }
          : r
      )
    );

    setLikingIds(prev => new Set([...prev, route.id]));

    try {
      const endpoint = isCurrentlyLiked 
        ? `/user-routes/${route.id}/unlike?user_id=${user.id}`
        : `/user-routes/${route.id}/like?user_id=${user.id}`;
      
      await apiPost(endpoint, {});
      
      console.log(`Successfully ${isCurrentlyLiked ? 'unliked' : 'liked'} route ${route.id}`);
    } catch (error) {
      console.error('Error toggling like:', error);
      
      // Revert optimistic update
      setRoutes(prev =>
        prev.map(r =>
          r.id === route.id
            ? { 
                ...r, 
                likes: isCurrentlyLiked ? r.likes + 1 : Math.max(0, r.likes - 1),
                is_liked_by_user: isCurrentlyLiked
              }
            : r
        )
      );
      
      if (!error.message?.includes('already liked') && !error.message?.includes("haven't liked")) {
        Alert.alert('Error', 'Failed to update like. Please try again.');
      }
    } finally {
      setLikingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(route.id);
        return newSet;
      });
    }
  };

  const handleViewRoute = (route) => {
    if (!route.route_points || route.route_points.length === 0) {
      Alert.alert('No Route Data', 'This route has no coordinates to display.');
      return;
    }

    // Calculate center and bounds
    const latitudes = route.route_points.map(p => p.latitude);
    const longitudes = route.route_points.map(p => p.longitude);
    const minLat = Math.min(...latitudes);
    const maxLat = Math.max(...latitudes);
    const minLng = Math.min(...longitudes);
    const maxLng = Math.max(...longitudes);
    
    const region = {
      latitude: (minLat + maxLat) / 2,
      longitude: (minLng + maxLng) / 2,
      latitudeDelta: Math.max(maxLat - minLat, 0.01) * 1.5,
      longitudeDelta: Math.max(maxLng - minLng, 0.01) * 1.5,
    };
    
    setModalRegion(region);
    setSelectedRoute(route);
  };

  const handleCloseMap = () => {
    setSelectedRoute(null);
    setModalRegion(null);
  };

  const zoomInModal = () => {
    if (modalMapRef.current && modalRegion) {
      const newRegion = {
        ...modalRegion,
        latitudeDelta: modalRegion.latitudeDelta / 2,
        longitudeDelta: modalRegion.longitudeDelta / 2,
      };
      setModalRegion(newRegion);
      modalMapRef.current.animateToRegion(newRegion, 300);
    }
  };

  const zoomOutModal = () => {
    if (modalMapRef.current && modalRegion) {
      const newRegion = {
        ...modalRegion,
        latitudeDelta: modalRegion.latitudeDelta * 2,
        longitudeDelta: modalRegion.longitudeDelta * 2,
      };
      setModalRegion(newRegion);
      modalMapRef.current.animateToRegion(newRegion, 300);
    }
  };

  const formatDistance = (meters) => {
    if (!meters) return '';
    if (meters < 1000) {
      return `${Math.round(meters)}m`;
    }
    return `${(meters / 1000).toFixed(1)}km`;
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '';
    const mins = Math.round(seconds / 60);
    if (mins < 60) {
      return `${mins}min`;
    }
    const hours = Math.floor(mins / 60);
    const remainingMins = mins % 60;
    return `${hours}h ${remainingMins}min`;
  };

  const getModeIcon = (mode) => {
    const icons = {
      walking: 'walk',
      driving: 'car',
      bicycling: 'bicycle',
      transit: 'train',
    };
    return icons[mode] || 'map';
  };

  const getModeColor = (mode) => {
    const colors = {
      walking: '#2BB673',
      driving: '#4C8BF5',
      bicycling: '#F4B400',
      transit: '#A16EF1',
    };
    return colors[mode] || '#888';
  };

  return (
    <SafeAreaView style={styles.root}>
      <HeaderBackButton onPress={() => navigation.goBack()} />

      <TouchableOpacity
        style={styles.fab}
        onPress={() => navigation.navigate('CreateRoute')}
        activeOpacity={0.7}
      >
        <Text style={styles.fabIcon}>＋</Text>
      </TouchableOpacity>

      <Text style={styles.title}>User Suggested Routes</Text>
      
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Ionicons 
          name="search" 
          size={20} 
          color={theme.colors.muted} 
          style={styles.searchIcon}
        />
        <TextInput
          style={[styles.searchInput, { 
            color: theme.colors.text,
            backgroundColor: theme.colors.card,
            borderColor: theme.colors.border
          }]}
          placeholder="Search routes..."
          placeholderTextColor={theme.colors.muted}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity 
            style={styles.clearButton}
            onPress={() => setSearchQuery('')}
          >
            <Ionicons name="close-circle" size={20} color={theme.colors.muted} />
          </TouchableOpacity>
        )}
      </View>
      
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.colors.accent} />
        </View>
      ) : (
        <FlatList
          data={filteredRoutes}
          keyExtractor={item => item.id.toString()}
          contentContainerStyle={styles.listContainer}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor={theme.colors.accent}
            />
          }
          renderItem={({ item }) => (
            <Card style={[styles.card, { backgroundColor: theme.colors.card, borderColor: theme.colors.border, borderWidth: StyleSheet.hairlineWidth }]}>
              <View style={styles.cardHeader}>
                <View style={styles.cardHeaderLeft}>
                  <View style={styles.cardTitleRow}>
                    <Text style={[styles.cardTitle, { color: theme.colors.text }]}>{item.title}</Text>
                    <View style={[styles.modeBadge, { backgroundColor: getModeColor(item.transport_mode) + '20' }]}>
                      <Ionicons name={getModeIcon(item.transport_mode)} size={14} color={getModeColor(item.transport_mode)} />
                    </View>
                  </View>
                  {(item.distance || item.duration) && (
                    <Text style={[styles.cardMeta, { color: theme.colors.muted }]}>
                      {item.distance && formatDistance(item.distance)}
                      {item.distance && item.duration && ' · '}
                      {item.duration && formatDuration(item.duration)}
                    </Text>
                  )}
                </View>
                <TouchableOpacity
                  style={styles.likeButton}
                  onPress={() => handleLike(item)}
                  disabled={likingIds.has(item.id)}
                >
                  <Ionicons
                    name={item.is_liked_by_user ? "heart" : "heart-outline"}
                    size={28}
                    color={item.is_liked_by_user ? "#FF3B30" : theme.colors.muted}
                  />
                  <Text style={[styles.likeCount, { color: theme.colors.text }]}>
                    {item.likes}
                  </Text>
                </TouchableOpacity>
              </View>
              
              {item.description && (
                <Text style={[styles.cardDescription, { color: theme.colors.text }]}>
                  {item.description}
                </Text>
              )}
              
              {/* Card Footer */}
              <View style={styles.cardFooter}>
                {item.created_by && (
                  <Text style={[styles.cardAuthor, { color: theme.colors.muted }]}>
                    Shared by {item.created_by}
                  </Text>
                )}
                
                <TouchableOpacity
                  style={styles.viewButton}
                  onPress={() => handleViewRoute(item)}
                >
                  <Ionicons name="map" size={18} color={theme.colors.accent} />
                  <Text style={[styles.viewButtonText, { color: theme.colors.accent }]}>
                    View Details
                  </Text>
                </TouchableOpacity>
              </View>
            </Card>
          )}
          ListEmptyComponent={
            <Text style={[styles.emptyText, { color: theme.colors.muted }]}>
              {searchQuery ? 'No routes match your search.' : 'No user routes yet. Share your best path!'}
            </Text>
          }
        />
      )}
      
      {/* Route Map Modal */}
      <Modal
        visible={selectedRoute !== null}
        animationType="slide"
        transparent={false}
        onRequestClose={handleCloseMap}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity
              onPress={handleCloseMap}
              style={styles.modalCloseButton}
            >
              <Ionicons name="close" size={28} color={theme.colors.text} />
            </TouchableOpacity>
            <Text style={[styles.modalTitle, { color: theme.colors.text }]}>
              {selectedRoute?.title || 'Route'}
            </Text>
          </View>
          
          {selectedRoute && modalRegion && (
            <View style={styles.modalMapWrapper}>
              <MapView
                provider={PROVIDER_GOOGLE}
                ref={modalMapRef}
                style={styles.modalMap}
                region={modalRegion}
                onRegionChangeComplete={(newRegion) => setModalRegion(newRegion)}
              >
                {/* Draw the route polyline */}
                {selectedRoute.route_points && selectedRoute.route_points.length > 1 && (
                  <Polyline
                    coordinates={selectedRoute.route_points.map(p => ({
                      latitude: p.latitude,
                      longitude: p.longitude
                    }))}
                    strokeWidth={4}
                    strokeColor={getModeColor(selectedRoute.transport_mode)}
                    lineCap="round"
                    lineJoin="round"
                  />
                )}
                
                {/* Start marker */}
                {selectedRoute.route_points && selectedRoute.route_points.length > 0 && (
                  <Marker
                    coordinate={{
                      latitude: selectedRoute.route_points[0].latitude,
                      longitude: selectedRoute.route_points[0].longitude,
                    }}
                    pinColor="green"
                    title="Start"
                  />
                )}
                
                {/* End marker */}
                {selectedRoute.route_points && selectedRoute.route_points.length > 1 && (
                  <Marker
                    coordinate={{
                      latitude: selectedRoute.route_points[selectedRoute.route_points.length - 1].latitude,
                      longitude: selectedRoute.route_points[selectedRoute.route_points.length - 1].longitude,
                    }}
                    pinColor="red"
                    title="End"
                  />
                )}
              </MapView>
              
              {/* Zoom Controls */}
              <View style={styles.modalZoomControls}>
                <TouchableOpacity style={styles.zoomButton} onPress={zoomInModal}>
                  <Ionicons name="add" size={24} color={theme.colors.text} />
                </TouchableOpacity>
                <TouchableOpacity style={styles.zoomButton} onPress={zoomOutModal}>
                  <Ionicons name="remove" size={24} color={theme.colors.text} />
                </TouchableOpacity>
              </View>
            </View>
          )}
          
          {/* Route Info */}
          {selectedRoute && (
            <ScrollView style={[styles.modalRouteInfo, { backgroundColor: theme.colors.card }]}>
              {selectedRoute.description && (
                <Text style={[styles.modalDescription, { color: theme.colors.text }]}>
                  {selectedRoute.description}
                </Text>
              )}
              <View style={styles.modalStats}>
                <View style={styles.modalStat}>
                  <Ionicons name={getModeIcon(selectedRoute.transport_mode)} size={20} color={theme.colors.accent} />
                  <Text style={[styles.modalStatText, { color: theme.colors.text }]}>
                    {selectedRoute.transport_mode}
                  </Text>
                </View>
                {selectedRoute.distance && (
                  <View style={styles.modalStat}>
                    <Ionicons name="location" size={20} color={theme.colors.accent} />
                    <Text style={[styles.modalStatText, { color: theme.colors.text }]}>
                      {formatDistance(selectedRoute.distance)}
                    </Text>
                  </View>
                )}
                {selectedRoute.duration && (
                  <View style={styles.modalStat}>
                    <Ionicons name="time" size={20} color={theme.colors.accent} />
                    <Text style={[styles.modalStatText, { color: theme.colors.text }]}>
                      {formatDuration(selectedRoute.duration)}
                    </Text>
                  </View>
                )}
              </View>
            </ScrollView>
          )}
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const createStyles = (theme) =>
  StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: theme.colors.background,
    },
    fab: {
      position: 'absolute',
      top: 52,
      right: 24,
      zIndex: 2,
      backgroundColor: theme.colors.card,
      borderRadius: 999,
      width: 48,
      height: 48,
      justifyContent: 'center',
      alignItems: 'center',
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: theme.mode === 'dark' ? 0.4 : 0.2,
      shadowRadius: 6,
      elevation: 3,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.colors.border,
    },
    fabIcon: {
      fontSize: 28,
      color: theme.colors.text,
      marginTop: -2,
    },
    title: {
      fontWeight: '800',
      fontSize: 22,
      marginLeft: 16,
      marginTop: 8,
      color: theme.colors.text,
      marginBottom: 12,
    },
    searchContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      marginHorizontal: 16,
      marginBottom: 12,
      backgroundColor: theme.colors.card,
      borderRadius: 12,
      borderWidth: 1,
      borderColor: theme.colors.border,
      paddingHorizontal: 12,
    },
    searchIcon: {
      marginRight: 8,
    },
    searchInput: {
      flex: 1,
      paddingVertical: 12,
      fontSize: 16,
    },
    clearButton: {
      padding: 4,
      marginLeft: 8,
    },
    loadingContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
    },
    listContainer: {
      padding: 16,
      paddingBottom: 32,
    },
    card: {
      borderRadius: 16,
      padding: 16,
      marginBottom: 12,
    },
    cardHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: 8,
    },
    cardHeaderLeft: {
      flex: 1,
      marginRight: 12,
    },
    cardTitleRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
    },
    cardTitle: {
      fontWeight: '700',
      fontSize: 16,
      flex: 1,
    },
    modeBadge: {
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 12,
    },
    cardMeta: {
      marginTop: 6,
      fontSize: 13,
    },
    cardDescription: {
      marginTop: 10,
      lineHeight: 20,
    },
    cardFooter: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginTop: 12,
      gap: 8,
    },
    cardAuthor: {
      fontSize: 12,
      fontStyle: 'italic',
      flex: 1,
    },
    viewButton: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 6,
      paddingVertical: 6,
      paddingHorizontal: 10,
      backgroundColor: theme.colors.background,
      borderRadius: 8,
      borderWidth: 1,
      borderColor: theme.colors.accent,
    },
    viewButtonText: {
      fontSize: 14,
      fontWeight: '600',
    },
    likeButton: {
      alignItems: 'center',
      justifyContent: 'center',
      paddingHorizontal: 8,
      paddingVertical: 4,
    },
    likeCount: {
      fontSize: 14,
      fontWeight: '600',
      marginTop: 2,
    },
    emptyText: {
      textAlign: 'center',
      marginTop: 32,
    },
    // Map Modal Styles
    modalContainer: {
      flex: 1,
      backgroundColor: theme.colors.background,
    },
    modalHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingTop: 60,
      paddingHorizontal: 16,
      paddingBottom: 16,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border,
    },
    modalCloseButton: {
      marginRight: 12,
    },
    modalTitle: {
      fontSize: 20,
      fontWeight: '700',
      flex: 1,
    },
    modalMapWrapper: {
      flex: 1,
      position: 'relative',
    },
    modalMap: {
      flex: 1,
    },
    modalZoomControls: {
      position: 'absolute',
      right: 10,
      top: 10,
      gap: 8,
    },
    zoomButton: {
      backgroundColor: theme.colors.card,
      width: 40,
      height: 40,
      borderRadius: 8,
      justifyContent: 'center',
      alignItems: 'center',
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.25,
      shadowRadius: 4,
      elevation: 5,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    modalRouteInfo: {
      maxHeight: 150,
      padding: 16,
      borderTopWidth: 1,
      borderTopColor: theme.colors.border,
    },
    modalDescription: {
      fontSize: 15,
      lineHeight: 22,
      marginBottom: 12,
    },
    modalStats: {
      flexDirection: 'row',
      gap: 16,
      flexWrap: 'wrap',
    },
    modalStat: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 6,
    },
    modalStatText: {
      fontSize: 14,
      fontWeight: '500',
    },
  });
