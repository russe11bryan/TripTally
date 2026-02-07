import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import HomePage from '../screens/HomePage';
import SavedPage from '../screens/SavedPage';
import ProfilePage from '../screens/ProfilePage';
import RecommendationPage from '../screens/RecommendationPage';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../context/ThemeContext';

const Tab = createBottomTabNavigator();
const TAB_ICONS = { Explore: 'map', Saved: 'heart', Suggest: 'chatbox', Profile: 'person' };

export default function MainTabs() {
  const { theme } = useTheme();
  const colors = theme.colors;

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarShowLabel: false,
        tabBarStyle: [
          styles.tabBar,
          {
            backgroundColor: colors.card,
            borderTopColor: colors.border,
          },
        ],
        tabBarIcon: ({ focused }) => {
          const iconName = TAB_ICONS[route.name];
          const tintColor = focused ? colors.accent : colors.muted;

          return (
            <View
              style={[
                styles.tabItem,
                focused && [{ backgroundColor: colors.pill }],
              ]}
            >
              <Ionicons name={iconName} size={20} color={tintColor} />
              <Text style={[styles.tabLabel, { color: tintColor }]}>{route.name}</Text>
            </View>
          );
        },
      })}
    >
      <Tab.Screen name="Explore" component={HomePage} />
      <Tab.Screen name="Saved" component={SavedPage} />
      <Tab.Screen name="Suggest" component={RecommendationPage} />
      <Tab.Screen name="Profile" component={ProfilePage} />
    </Tab.Navigator>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: '#273B4A',
    borderTopColor: 'transparent',
    paddingVertical: 15,
    height: 84,
  },
  tabItem: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 18,
    paddingVertical: 8,
    borderRadius: 14,
  },
  tabItemActive: {
    backgroundColor: '#ffffff',
  },
  tabLabel: {
    marginTop: 4,
    fontSize: 12,
    fontWeight: '600',
  },
});
