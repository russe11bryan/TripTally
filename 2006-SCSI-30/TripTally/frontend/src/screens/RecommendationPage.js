import React, { useMemo, useState, useEffect, useCallback } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator, RefreshControl, Alert, TextInput, Modal } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import { useFocusEffect } from '@react-navigation/native';
import Card from '../components/Card';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { apiGet, apiPost } from '../services/api';

export default function RecommendationPage({ navigation }) {
  const { theme } = useTheme();
  const { user } = useAuth();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [recommendations, setRecommendations] = useState([]);
  const [filteredRecommendations, setFilteredRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [likingIds, setLikingIds] = useState(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLocation, setSelectedLocation] = useState(null); // For map modal
  const [modalRegion, setModalRegion] = useState(null); // For map zoom
  const modalMapRef = React.useRef(null);

  const fetchRecommendations = async (isRefresh = false) => {
    try {
      if (!isRefresh) setLoading(true);
      
      // Fetch all suggestions with user's like status
      const userId = user?.id;
      const url = userId ? `/suggestions?user_id=${userId}` : '/suggestions';
      const data = await apiGet(url);
      
      console.log('Fetched suggestions:', data.length);
      
      // Sort by likes (highest first), then by created_at (newest first)
      const sorted = data.sort((a, b) => {
        if (b.likes !== a.likes) {
          return b.likes - a.likes;
        }
        return new Date(b.created_at) - new Date(a.created_at);
      });
      
      setRecommendations(sorted);
      setFilteredRecommendations(sorted);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      Alert.alert('Error', 'Failed to load recommendations. Please try again.');
    } finally {
      setLoading(false);
      if (isRefresh) setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [user?.id]);

  // Refresh data when screen comes into focus (e.g., after adding a new recommendation)
  useFocusEffect(
    useCallback(() => {
      console.log('RecommendationPage focused - refreshing data');
      fetchRecommendations();
    }, [user?.id])
  );

  useEffect(() => {
    // Filter recommendations based on search query
    if (searchQuery.trim() === '') {
      setFilteredRecommendations(recommendations);
    } else {
      const query = searchQuery.toLowerCase();
      const filtered = recommendations.filter(rec =>
        rec.title.toLowerCase().includes(query) ||
        rec.category.toLowerCase().includes(query) ||
        rec.description.toLowerCase().includes(query) ||
        (rec.added_by && rec.added_by.toLowerCase().includes(query))
      );
      setFilteredRecommendations(filtered);
    }
  }, [searchQuery, recommendations]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchRecommendations(true);
  };

  const handleLike = async (suggestion) => {
    // Check if user is logged in
    if (!user?.id) {
      Alert.alert('Login Required', 'Please log in to like recommendations.');
      return;
    }

    // Prevent multiple simultaneous likes on the same suggestion
    if (likingIds.has(suggestion.id)) return;

    const isCurrentlyLiked = suggestion.is_liked_by_user;

    // Optimistically update UI immediately for instant feedback
    setRecommendations(prev =>
      prev.map(rec =>
        rec.id === suggestion.id
          ? { 
              ...rec, 
              likes: isCurrentlyLiked ? rec.likes - 1 : rec.likes + 1,
              is_liked_by_user: !isCurrentlyLiked
            }
          : rec
      )
    );

    // Mark as processing
    setLikingIds(prev => new Set([...prev, suggestion.id]));

    try {
      // Send like/unlike to backend (toggle action)
      const endpoint = isCurrentlyLiked 
        ? `/suggestions/${suggestion.id}/unlike`
        : `/suggestions/${suggestion.id}/like`;
      
      await apiPost(endpoint, { user_id: user.id });
      
      console.log(`Successfully ${isCurrentlyLiked ? 'unliked' : 'liked'} suggestion ${suggestion.id}`);
      
      // Success - optimistic update was correct, no need to update again
    } catch (error) {
      console.error('Error toggling like:', error);
      
      // Revert optimistic update on error
      setRecommendations(prev =>
        prev.map(rec =>
          rec.id === suggestion.id
            ? { 
                ...rec, 
                likes: isCurrentlyLiked ? rec.likes + 1 : Math.max(0, rec.likes - 1),
                is_liked_by_user: isCurrentlyLiked
              }
            : rec
        )
      );
      
      // Only show alert for unexpected errors, not for normal toggle conflicts
      if (!error.message?.includes('already liked') && !error.message?.includes("haven't liked")) {
        Alert.alert('Error', 'Failed to update like. Please try again.');
      }
    } finally {
      // Remove from processing set
      setLikingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(suggestion.id);
        return newSet;
      });
    }
  };

  const handleOpenMap = (item) => {
    const region = {
      latitude: item.latitude,
      longitude: item.longitude,
      latitudeDelta: 0.01,
      longitudeDelta: 0.01,
    };
    setModalRegion(region);
    setSelectedLocation({
      latitude: item.latitude,
      longitude: item.longitude,
      title: item.title,
      locationName: item.location_name
    });
  };

  const handleCloseMap = () => {
    setSelectedLocation(null);
    setModalRegion(null);
  };

  const handleGetDirections = () => {
    if (selectedLocation) {
      // Close the modal first
      handleCloseMap();
      
      // Navigate to DirectionsPage with the destination pre-filled
      navigation.navigate('Directions', {
        destination: {
          latitude: selectedLocation.latitude,
          longitude: selectedLocation.longitude,
          name: selectedLocation.locationName || selectedLocation.title,
        }
      });
    }
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

  const handleModalRegionChange = (newRegion) => {
    setModalRegion(newRegion);
  };

  return (
    <View style={styles.root}>
      <TouchableOpacity
        style={styles.fab}
        onPress={() => navigation.navigate('AddRecommendation')}
      >
        <Text style={styles.fabIcon}>＋</Text>
      </TouchableOpacity>

      <Text style={styles.title}>Recommended For You</Text>
      
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
          placeholder="Search recommendations..."
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
          data={filteredRecommendations}
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
            <Card style={styles.card}>
              <View style={styles.cardHeader}>
                <View style={styles.cardHeaderLeft}>
                  <Text style={[styles.cardTitle, { color: theme.colors.text }]}>{item.title}</Text>
                  <Text style={[styles.cardMeta, { color: theme.colors.muted }]}>{item.category}</Text>
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
              
              <Text style={[styles.cardDescription, { color: theme.colors.text }]}>
                {item.description}
              </Text>
              
              {/* Card Footer with author and location button */}
              {(item.added_by || (item.latitude && item.longitude)) && (
                <View style={styles.cardFooter}>
                  {item.added_by && (
                    <Text style={[styles.cardAuthor, { color: theme.colors.muted }]}>
                      Shared by {item.added_by}
                    </Text>
                  )}
                  
                  {/* Show location button in bottom right */}
                  {item.latitude && item.longitude && (
                    <TouchableOpacity
                      style={styles.locationButton}
                      onPress={() => handleOpenMap(item)}
                    >
                      <Ionicons name="location" size={18} color={theme.colors.accent} />
                      <Text style={[styles.locationButtonText, { color: theme.colors.accent }]}>
                        {item.location_name || 'Show on Map'}
                      </Text>
                    </TouchableOpacity>
                  )}
                </View>
              )}
            </Card>
          )}
          ListEmptyComponent={
            <Text style={[styles.emptyText, { color: theme.colors.muted }]}>
              {searchQuery ? 'No recommendations match your search.' : 'No recommendations yet. Be the first to share one!'}
            </Text>
          }
        />
      )}
      
      {/* Map Modal */}
      <Modal
        visible={selectedLocation !== null}
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
              {selectedLocation?.title || 'Location'}
            </Text>
          </View>
          
          {selectedLocation && modalRegion && (
            <View style={styles.modalMapWrapper}>
              <MapView
                provider={PROVIDER_GOOGLE}
                ref={modalMapRef}
                style={styles.modalMap}
                region={modalRegion}
                onRegionChangeComplete={handleModalRegionChange}
              >
                <Marker
                  coordinate={{
                    latitude: selectedLocation.latitude,
                    longitude: selectedLocation.longitude,
                  }}
                  title={selectedLocation.title}
                  description={selectedLocation.locationName}
                />
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
          
          {selectedLocation?.locationName && (
            <View style={[styles.modalLocationInfo, { backgroundColor: theme.colors.card }]}>
              <Ionicons name="location" size={20} color={theme.colors.accent} />
              <Text style={[styles.modalLocationText, { color: theme.colors.text }]}>
                {selectedLocation.locationName}
              </Text>
            </View>
          )}
          
          {/* Get Directions Button */}
          <TouchableOpacity
            style={[styles.directionsButton, { backgroundColor: theme.colors.accent }]}
            onPress={handleGetDirections}
          >
            <Ionicons name="navigate" size={22} color="#FFFFFF" />
            <Text style={styles.directionsButtonText}>Get Directions</Text>
          </TouchableOpacity>
        </View>
      </Modal>
    </View>
  );
}

const createStyles = (theme) =>
  StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: theme.colors.background,
      paddingTop: 60,
    },
    fab: {
      position: 'absolute',
      top: 52,
      right: 24,
      zIndex: 2,
      backgroundColor: theme.colors.card,
      borderRadius: 999,
      width: 35,
      height: 35,
      justifyContent: 'center',
      alignItems: 'center',
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: theme.mode === 'dark' ? 0.35 : 0.2,
      shadowRadius: 6,
      elevation: 3,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.colors.border,
    },
    fabIcon: {
      fontSize: 20,
      color: theme.colors.text,
      marginTop: -2,
    },
    title: {
      fontWeight: '800',
      fontSize: 22,
      marginLeft: 16,
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
    cardTitle: {
      fontWeight: '700',
      fontSize: 16,
    },
    cardMeta: {
      marginTop: 6,
      fontSize: 13,
    },
    cardDescription: {
      marginTop: 8,
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
    locationButton: {
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
    locationButtonText: {
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
      marginTop: 40,
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
    modalLocationInfo: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
      padding: 16,
      borderTopWidth: 1,
      borderTopColor: theme.colors.border,
    },
    modalLocationText: {
      fontSize: 16,
      fontWeight: '500',
    },
    directionsButton: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 10,
      margin: 16,
      marginTop: 0,
      padding: 16,
      borderRadius: 12,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.2,
      shadowRadius: 4,
      elevation: 3,
    },
    directionsButtonText: {
      color: '#FFFFFF',
      fontSize: 18,
      fontWeight: '700',
    },
  });
