import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, FlatList, ActivityIndicator, Alert, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { apiGet, apiPost } from '../services/api';
import Card from '../components/Card';

export default function SelectListPage({ route, navigation }) {
  const { place } = route.params;
  const { user } = useAuth();
  const { theme } = useTheme();
  const [lists, setLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchLists();
  }, [user?.id]);

  const fetchLists = async () => {
    if (!user?.id) {
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      const data = await apiGet(`/saved/lists/user/${user.id}`);
      setLists(data);
    } catch (error) {
      console.error('Error fetching saved lists:', error);
      setLists([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectList = async (list) => {
    if (!place || !list) return;

    try {
      setSaving(true);
      await apiPost('/saved/places', {
        list_id: list.id,
        name: place.name,
        address: place.address,
        latitude: place.latitude,
        longitude: place.longitude,
      });

      Alert.alert(
        'Place Saved',
        `"${place.name}" has been added to "${list.name}"`,
        [
          {
            text: 'OK',
            onPress: () => navigation.navigate('SavePlace', { list }),
          },
        ]
      );
    } catch (error) {
      console.error('Error saving place:', error);
      Alert.alert('Error', 'Failed to save place. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const styles = createStyles(theme.colors);

  return (
    <View style={styles.root}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={24} color={theme.colors.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Select a List</Text>
        <TouchableOpacity onPress={() => navigation.navigate('NewList', { returnPlace: place })}>
          <Ionicons name="add-circle-outline" size={24} color={theme.colors.accent} />
        </TouchableOpacity>
      </View>

      {/* Place Info */}
      <View style={styles.placeInfo}>
        <View style={styles.placeIconContainer}>
          <Ionicons name="location" size={24} color={theme.colors.accent} />
        </View>
        <View style={styles.placeDetails}>
          <Text style={styles.placeName}>{place?.name}</Text>
          {place?.address && (
            <Text style={styles.placeAddress} numberOfLines={2}>
              {place.address}
            </Text>
          )}
        </View>
      </View>

      {/* Lists */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.colors.accent} />
        </View>
      ) : lists.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Ionicons name="list-outline" size={64} color={theme.colors.muted} />
          <Text style={styles.emptyText}>No lists yet</Text>
          <Text style={styles.emptySubtext}>Create your first list to save places</Text>
          <TouchableOpacity 
            style={styles.createButton}
            onPress={() => navigation.navigate('NewList', { returnPlace: place })}
          >
            <Text style={styles.createButtonText}>Create New List</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={lists}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContainer}
          renderItem={({ item }) => (
            <TouchableOpacity
              onPress={() => handleSelectList(item)}
              disabled={saving}
            >
              <Card style={styles.listCard}>
                <View style={styles.listIconContainer}>
                  <Ionicons name="list" size={24} color={theme.colors.accent} />
                </View>
                <View style={styles.listInfo}>
                  <Text style={styles.listName}>{item.name}</Text>
                  <Text style={styles.listMeta}>
                    {item.place_count || 0} {item.place_count === 1 ? 'place' : 'places'}
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={20} color={theme.colors.muted} />
              </Card>
            </TouchableOpacity>
          )}
        />
      )}

      {saving && (
        <View style={styles.savingOverlay}>
          <ActivityIndicator size="large" color={theme.colors.accent} />
          <Text style={styles.savingText}>Saving...</Text>
        </View>
      )}
    </View>
  );
}

const createStyles = (colors) =>
  StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: colors.background,
    },
    header: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingHorizontal: 16,
      paddingTop: 60,
      paddingBottom: 16,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: colors.border,
      backgroundColor: colors.background,
    },
    title: {
      fontSize: 18,
      fontWeight: '700',
      color: colors.text,
    },
    placeInfo: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 16,
      marginHorizontal: 16,
      marginTop: 16,
      backgroundColor: colors.card,
      borderRadius: 12,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.border,
    },
    placeIconContainer: {
      width: 48,
      height: 48,
      borderRadius: 24,
      backgroundColor: colors.accent + '20',
      justifyContent: 'center',
      alignItems: 'center',
      marginRight: 12,
    },
    placeDetails: {
      flex: 1,
    },
    placeName: {
      fontSize: 16,
      fontWeight: '700',
      color: colors.text,
      marginBottom: 4,
    },
    placeAddress: {
      fontSize: 14,
      color: colors.muted,
    },
    loadingContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
    },
    emptyContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      paddingHorizontal: 32,
    },
    emptyText: {
      fontSize: 18,
      fontWeight: '700',
      color: colors.text,
      marginTop: 16,
    },
    emptySubtext: {
      fontSize: 14,
      color: colors.muted,
      marginTop: 8,
      textAlign: 'center',
    },
    createButton: {
      marginTop: 24,
      backgroundColor: colors.accent,
      paddingVertical: 14,
      paddingHorizontal: 24,
      borderRadius: 12,
    },
    createButtonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: '700',
    },
    listContainer: {
      padding: 16,
    },
    listCard: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 12,
      marginBottom: 12,
    },
    listIconContainer: {
      width: 44,
      height: 44,
      borderRadius: 22,
      backgroundColor: colors.accent + '20',
      justifyContent: 'center',
      alignItems: 'center',
      marginRight: 12,
    },
    listInfo: {
      flex: 1,
    },
    listName: {
      fontSize: 16,
      fontWeight: '700',
      color: colors.text,
      marginBottom: 2,
    },
    listMeta: {
      fontSize: 14,
      color: colors.muted,
    },
    savingOverlay: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      justifyContent: 'center',
      alignItems: 'center',
    },
    savingText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: '600',
      marginTop: 12,
    },
  });
