import React, {useState} from 'react';
import { View, Text, TouchableOpacity, TextInput, Alert, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import HeaderBackButton from '../components/HeaderBackButton';
import useThemedStyles from '../hooks/useThemedStyles';
import { useAuth } from '../context/AuthContext';
import { apiPost } from '../services/api';

export default function ReportTechnicalIssue({ navigation }) {
  const { user, token } = useAuth();
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const { styles, theme } = useThemedStyles(({ colors }) => ({
    root:{flex:1, backgroundColor:colors.background, paddingTop:48 },
    scrollContent: { paddingBottom: 24 },
    categoryTitle:{ fontWeight:'700', fontSize:32, marginLeft:16, marginBottom:12, color: colors.text },
    categoryGrid:{
      marginHorizontal:16,
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 12,
      marginBottom:24,
    },
    categoryCard:{
      flex: 1,
      minWidth: '45%',
      backgroundColor: colors.card,
      borderRadius:16,
      padding:16,
      borderWidth: 2,
      borderColor: colors.border,
      alignItems:'center',
      justifyContent:'center',
      minHeight: 100,
    },
    categoryCardActive:{
      backgroundColor: colors.accent,
      borderColor: colors.accent,
    },
    categoryIcon: {
      marginBottom: 8,
    },
    categoryText:{
      fontWeight:'600',
      fontSize:15,
      textAlign: 'center',
      color: colors.text,
    },
    categoryTextActive:{
      color:'#fff',
    },
    sectionTitle:{
      fontWeight:'700',
      fontSize:32,
      marginLeft:16,
      marginBottom:5,
      color: colors.text,
    },
    descBox:{
      marginHorizontal:16,
      height:120,
      backgroundColor: colors.card,
      borderRadius:16,
      marginBottom:24,
      padding:12,
      borderWidth:1,
      borderColor: colors.border,
    },
    descInput:{ fontSize:18, color: colors.text, flex:1, textAlignVertical:'top' },
    uploadButton:{
      backgroundColor: colors.accent,
      paddingVertical:12,
      paddingHorizontal:38,
      borderRadius:32,
      alignSelf:'center',
      marginTop:16,
      marginBottom:32,
      flexDirection:'row',
      alignItems:'center',
      gap:8,
    },
    uploadLabel:{ fontSize:20, fontWeight:'700', color:'#fff' },
    uploadIcon:{ fontSize:20 },
  }));

  const categories = [
    { name: "Inaccurate Metrics/Routes", icon: "analytics" },
    { name: "Bugs/Technical Issues", icon: "bug" },
    { name: "Abuse of Platform", icon: "warning" },
    { name: "Others", icon: "ellipsis-horizontal" }
  ];

  const handleUpload = async () => {
    if (!selectedCategory) {
      Alert.alert("Error", "Please select an issue category");
      return;
    }
    if (!description.trim()) {
      Alert.alert("Error", "Please provide a description");
      return;
    }

    setUploading(true);
    try {
      // Ensure added_by is always a string
      const username = user?.username || user?.display_name || user?.email || null;
      const addedBy = username ? String(username) : 'Anonymous';
      
      console.log('Submitting technical report:', {
        category: selectedCategory,
        user_id: user?.id,
        added_by: addedBy,
        added_by_type: typeof addedBy,
      });
      
      await apiPost('/reports/technical', {
        category: selectedCategory,
        description: description.trim(),
        user_id: user?.id || null,
        added_by: addedBy,
      }, { token });

      Alert.alert(
        "Success",
        "Technical report submitted successfully!",
        [
          {
            text: "OK",
            onPress: () => navigation.goBack()
          }
        ]
      );
    } catch (error) {
      console.error('Error submitting technical report:', error);
      Alert.alert(
        "Error",
        error.message || "Failed to submit report. Please try again."
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <View style={styles.root}>
      <HeaderBackButton onPress={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Category Title */}
        <Text style={styles.categoryTitle}>
          Category
        </Text>

        {/* Categories grid (2x2 with icons) */}
        <View style={styles.categoryGrid}>
          {categories.map((cat) => (
            <TouchableOpacity
              key={cat.name}
              style={[
                styles.categoryCard,
                selectedCategory === cat.name && styles.categoryCardActive,
              ]}
              activeOpacity={0.8}
              onPress={() => setSelectedCategory(cat.name)}
            >
              <Ionicons
                name={cat.icon}
                size={32}
                color={selectedCategory === cat.name ? '#fff' : theme.colors.accent}
                style={styles.categoryIcon}
              />
              <Text
                style={[
                  styles.categoryText,
                  selectedCategory === cat.name && styles.categoryTextActive,
                ]}
              >
                {cat.name}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Add Description */}
        <Text style={styles.sectionTitle}>
          Add Description
        </Text>
        <View style={styles.descBox}>
          <TextInput
            value={description}
            onChangeText={setDescription}
            placeholder="Type here"
            placeholderTextColor={theme.colors.muted}
            multiline
            style={styles.descInput}
          />
        </View>

        {/* Upload Button */}
        <TouchableOpacity
          style={styles.uploadButton}
          onPress={handleUpload}
          disabled={uploading}
        >
          {uploading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.uploadLabel}>Upload</Text>
          )}
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}
