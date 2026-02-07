import React, { useMemo, useState, useEffect, useCallback } from 'react';
import { View, Text, TouchableOpacity, FlatList, StyleSheet, SafeAreaView, ActivityIndicator, RefreshControl, Alert, Modal } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from '@react-navigation/native';
import MapView, { Marker } from 'react-native-maps';
import Card from '../components/Card';
import HeaderBackButton from '../components/HeaderBackButton';
import { useTheme } from '../context/ThemeContext';
import { apiGet } from '../services/api';

export default function IncidentReportPage({ navigation }) {
  const { theme } = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [showMapModal, setShowMapModal] = useState(false);

  const fetchIncidents = async (isRefresh = false) => {
    try {
      if (!isRefresh) setLoading(true);
      
      // Fetch active traffic alerts from backend
      const data = await apiGet('/traffic-alerts?status=active');
      
      console.log('Fetched incidents:', data.length);
      
      // Sort by created_at (newest first)
      const sorted = data.sort((a, b) => {
        return new Date(b.created_at) - new Date(a.created_at);
      });
      
      setIncidents(sorted);
    } catch (error) {
      console.error('Error fetching incidents:', error);
      Alert.alert('Error', 'Failed to load incidents. Please try again.');
    } finally {
      setLoading(false);
      if (isRefresh) setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, []);

  // Refresh when screen comes into focus
  useFocusEffect(
    useCallback(() => {
      console.log('IncidentReportPage focused - refreshing data');
      fetchIncidents();
    }, [])
  );

  const handleRefresh = () => {
    setRefreshing(true);
    fetchIncidents(true);
  };

  const getIncidentIcon = (obstructionType) => {
    switch (obstructionType) {
      case 'Traffic':
        return 'car-outline';
      case 'Accident':
        return 'warning-outline';
      case 'Road Closure':
        return 'close-circle-outline';
      case 'Police':
        return 'shield-checkmark-outline';
      default:
        return 'alert-circle-outline';
    }
  };

  const getIncidentColor = (obstructionType) => {
    switch (obstructionType) {
      case 'Traffic':
        return '#FF6B35';
      case 'Accident':
        return '#E63946';
      case 'Road Closure':
        return '#9D4EDD';
      case 'Police':
        return '#0077B6';
      default:
        return theme.colors.accent;
    }
  };

  const handleDropdown = (action) => {
    setShowDropdown(false);
    if (action === 'traffic') {
      navigation.navigate('ReportRoadIncident');
    }
    if (action === 'technical') {
      navigation.navigate('ReportTechnicalIssue');
    }
  };

  return (
    <SafeAreaView style={styles.root}>
      <HeaderBackButton onPress={() => navigation.goBack()} />

      <TouchableOpacity
        style={styles.fab}
        onPress={() => setShowDropdown(!showDropdown)}
        activeOpacity={0.7}
      >
        <Ionicons name="add" size={28} color={theme.colors.text} />
      </TouchableOpacity>

      {showDropdown && (
        <View style={styles.menu}>
          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => handleDropdown('traffic')}
          >
            <Ionicons name="car-sport" size={20} color={theme.colors.accent} style={styles.menuIcon} />
            <Text style={styles.menuLabel}>Report Traffic Incident</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => handleDropdown('technical')}
          >
            <Ionicons name="warning" size={20} color={theme.colors.accent} style={styles.menuIcon} />
            <Text style={styles.menuLabel}>Report Technical Issue</Text>
          </TouchableOpacity>
        </View>
      )}

      <Text style={styles.title}>Incident Reports</Text>
      
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.colors.accent} />
        </View>
      ) : (
        <FlatList
          data={incidents}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContainer}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor={theme.colors.accent}
            />
          }
          renderItem={({ item }) => {
            const iconName = getIncidentIcon(item.obstruction_type);
            const iconColor = getIncidentColor(item.obstruction_type);
            const timeAgo = item.created_at 
              ? new Date(item.created_at).toLocaleString()
              : 'Unknown time';
            
            return (
              <Card style={styles.card}>
                <View style={styles.cardHeader}>
                  <View style={[styles.iconContainer, { backgroundColor: iconColor + '20' }]}>
                    <Ionicons name={iconName} size={24} color={iconColor} />
                  </View>
                  <View style={styles.cardHeaderText}>
                    <Text style={[styles.cardTitle, { color: theme.colors.text }]}>
                      {item.obstruction_type}
                    </Text>
                    <Text style={[styles.cardMeta, { color: theme.colors.muted }]}>
                      {timeAgo}
                    </Text>
                  </View>
                </View>
                
                {item.location_name && (
                  <View style={styles.locationRow}>
                    <Ionicons name="location-outline" size={16} color={theme.colors.muted} />
                    <Text style={[styles.cardMeta, { color: theme.colors.muted, marginLeft: 6 }]}>
                      {item.location_name}
                    </Text>
                  </View>
                )}
                
                <View style={styles.rowBetween}>
                  <Text style={[styles.statusBadge, { 
                    color: item.status === 'active' ? '#10B981' : theme.colors.muted,
                    backgroundColor: item.status === 'active' ? '#10B98120' : theme.colors.card
                  }]}>
                    {item.status.toUpperCase()}
                  </Text>
                  <TouchableOpacity onPress={() => {
                    setSelectedIncident(item);
                    setShowMapModal(true);
                  }}>
                    <Text style={[styles.link, { color: theme.colors.accent }]}>Show On Map</Text>
                  </TouchableOpacity>
                </View>
              </Card>
            );
          }}
          ListEmptyComponent={
            <Text style={[styles.emptyText, { color: theme.colors.muted }]}>
              No incident reports yet. Be the first to share!
            </Text>
          }
        />
      )}

      {/* Map Modal */}
      <Modal
        visible={showMapModal}
        animationType="slide"
        transparent={false}
        onRequestClose={() => setShowMapModal(false)}
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity
              onPress={() => setShowMapModal(false)}
              style={styles.closeButton}
            >
              <Ionicons name="close" size={28} color={theme.colors.text} />
            </TouchableOpacity>
            <Text style={[styles.modalTitle, { color: theme.colors.text }]}>
              Incident Location
            </Text>
            <View style={{ width: 28 }} />
          </View>

          {selectedIncident && (
            <>
              <View style={styles.modalInfo}>
                <View style={styles.modalInfoRow}>
                  <View style={[styles.iconContainer, { 
                    backgroundColor: getIncidentColor(selectedIncident.obstruction_type) + '20' 
                  }]}>
                    <Ionicons 
                      name={getIncidentIcon(selectedIncident.obstruction_type)} 
                      size={20} 
                      color={getIncidentColor(selectedIncident.obstruction_type)} 
                    />
                  </View>
                  <View style={{ flex: 1, marginLeft: 12 }}>
                    <Text style={[styles.modalIncidentType, { color: theme.colors.text }]}>
                      {selectedIncident.obstruction_type}
                    </Text>
                    {selectedIncident.location_name && (
                      <Text style={[styles.modalLocationName, { color: theme.colors.muted }]}>
                        {selectedIncident.location_name}
                      </Text>
                    )}
                  </View>
                </View>
              </View>

              <MapView
                style={styles.map}
                initialRegion={{
                  latitude: selectedIncident.latitude,
                  longitude: selectedIncident.longitude,
                  latitudeDelta: 0.01,
                  longitudeDelta: 0.01,
                }}
              >
                <Marker
                  coordinate={{
                    latitude: selectedIncident.latitude,
                    longitude: selectedIncident.longitude,
                  }}
                  title={selectedIncident.obstruction_type}
                  description={selectedIncident.location_name || 'Reported incident'}
                >
                  <View style={[styles.markerContainer, { 
                    backgroundColor: getIncidentColor(selectedIncident.obstruction_type) 
                  }]}>
                    <Ionicons 
                      name={getIncidentIcon(selectedIncident.obstruction_type)} 
                      size={20} 
                      color="white" 
                    />
                  </View>
                </Marker>
              </MapView>
            </>
          )}
        </SafeAreaView>
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
      shadowOpacity: theme.mode === 'dark' ? 0.35 : 0.2,
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
    menu: {
      position: 'absolute',
      top: 104,
      right: 24,
      zIndex: 3,
      backgroundColor: theme.colors.card,
      borderRadius: 16,
      paddingVertical: 6,
      width: 240,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: theme.mode === 'dark' ? 0.35 : 0.2,
      shadowRadius: 10,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.colors.border,
    },
    menuItem: {
      padding: 16,
      flexDirection: 'row',
      alignItems: 'center',
    },
    menuIcon: {
      marginRight: 10,
    },
    menuLabel: {
      fontSize: 16,
      color: theme.colors.text,
    },
    title: {
      fontWeight: '800',
      fontSize: 22,
      marginLeft: 16,
      marginTop: 8,
      marginBottom: 8,
      color: theme.colors.text,
    },
    loadingContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      paddingTop: 100,
    },
    listContainer: {
      padding: 16,
    },
    card: {
      marginBottom: 12,
    },
    cardHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
    },
    iconContainer: {
      width: 48,
      height: 48,
      borderRadius: 24,
      justifyContent: 'center',
      alignItems: 'center',
      marginRight: 12,
    },
    cardHeaderText: {
      flex: 1,
    },
    cardTitle: {
      fontWeight: '700',
      fontSize: 18,
    },
    cardMeta: {
      marginTop: 4,
      fontSize: 14,
    },
    locationRow: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
    },
    rowBetween: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginTop: 6,
    },
    statusBadge: {
      fontSize: 12,
      fontWeight: '700',
      paddingHorizontal: 10,
      paddingVertical: 4,
      borderRadius: 12,
    },
    tag: {
      fontWeight: '600',
    },
    link: {
      fontWeight: '600',
      fontSize: 14,
    },
    emptyText: {
      textAlign: 'center',
      marginTop: 32,
    },
    modalContainer: {
      flex: 1,
      backgroundColor: theme.colors.background,
    },
    modalHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingHorizontal: 16,
      paddingVertical: 12,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: theme.colors.border,
    },
    closeButton: {
      padding: 4,
    },
    modalTitle: {
      fontSize: 18,
      fontWeight: '700',
    },
    modalInfo: {
      backgroundColor: theme.colors.card,
      padding: 16,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: theme.colors.border,
    },
    modalInfoRow: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    modalIncidentType: {
      fontSize: 16,
      fontWeight: '700',
    },
    modalLocationName: {
      fontSize: 14,
      marginTop: 4,
    },
    map: {
      flex: 1,
    },
    markerContainer: {
      width: 36,
      height: 36,
      borderRadius: 18,
      justifyContent: 'center',
      alignItems: 'center',
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.3,
      shadowRadius: 4,
      elevation: 5,
    },
  });
