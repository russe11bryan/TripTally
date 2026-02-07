import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import WelcomePage from '../screens/WelcomePage';
import SignIn from '../screens/SignIn';
import CreateAccount from '../screens/CreateAccount';
import MainTabs from './MainTabs';
import SearchPage from '../screens/SearchPage';
import LocationPage from '../screens/LocationPage';
import DirectionsPage from '../screens/DirectionsPage';
import ComparePage from '../screens/ComparePage';
import NewList from '../screens/NewList';
import SavePlace from '../screens/SavePlace';
import SelectListPage from '../screens/SelectListPage';
import AddPlaceToList from '../screens/AddPlaceToList';
import SetLocationPage from '../screens/SetLocationPage';
import CreateRoute from '../screens/CreateRoute';
import TransportDetailsPage from '../screens/TransportDetailsPage';
import ReportRoadIncident from '../screens/ReportRoadIncident';
import ReportTechnicalIssue from '../screens/ReportTechnicalIssue'; 
import AddRecommendationPage from '../screens/AddRecommendationPage';
import IncidentReportPage from '../screens/IncidentReportPage';
import UserSuggestedRoutePage from '../screens/UserSuggestedRoutePage';
import MyAccountPage from '../screens/MyAccountPage';
import PrivacyPage from '../screens/PrivacyPage';
import SecurityPage from '../screens/SecurityPage';
import SettingsPage from '../screens/SettingsPage';
import NearbyPlacesMap from '../screens/NearbyPlacesMap';
import NavigationView from '../screens/NavigationView';


const AuthStackNavigator = createNativeStackNavigator();
const AppStackNavigator = createNativeStackNavigator();

export function SignedOutStack() {
  return (
    <AuthStackNavigator.Navigator screenOptions={{ headerShown: false }}>
      <AuthStackNavigator.Screen name="Welcome" component={WelcomePage} />
      <AuthStackNavigator.Screen name="SignIn" component={SignIn} />
      <AuthStackNavigator.Screen name="CreateAccount" component={CreateAccount} />
    </AuthStackNavigator.Navigator>
  );
}

export function SignedInStack() {
  return (
    <AppStackNavigator.Navigator screenOptions={{ headerShown: false }}>
      <AppStackNavigator.Screen name="MainTabs" component={MainTabs} />
      {/* Non-tab screens */}
      <AppStackNavigator.Screen name="Search" component={SearchPage} />
      <AppStackNavigator.Screen name="NearbyPlacesMap" component={NearbyPlacesMap} />
      <AppStackNavigator.Screen name="Location" component={LocationPage} />
      <AppStackNavigator.Screen name="Directions" component={DirectionsPage} />
      
  <AppStackNavigator.Screen
  name="NavigationView"
  component={NavigationView}
  options={{ headerShown: false }}
/>

      <AppStackNavigator.Screen name="Compare" component={ComparePage} />
      <AppStackNavigator.Screen name="NewList" component={NewList} />
      <AppStackNavigator.Screen name="SelectList" component={SelectListPage} />
      <AppStackNavigator.Screen name="SavePlace" component={SavePlace} />
      <AppStackNavigator.Screen name="AddPlaceToList" component={AddPlaceToList} />
      <AppStackNavigator.Screen name="SetLocation" component={SetLocationPage} />
      <AppStackNavigator.Screen name="CreateRoute" component={CreateRoute} />
      <AppStackNavigator.Screen name="TransportDetails" component={TransportDetailsPage} />
      <AppStackNavigator.Screen name="ReportRoadIncident" component={ReportRoadIncident} />
      <AppStackNavigator.Screen name="IncidentReportPage" component={IncidentReportPage} />
      <AppStackNavigator.Screen name="UserSuggestedRoutePage" component={UserSuggestedRoutePage} />
      <AppStackNavigator.Screen name="ReportTechnicalIssue" component={ReportTechnicalIssue} />
      <AppStackNavigator.Screen name="AddRecommendation" component={AddRecommendationPage} />
      <AppStackNavigator.Screen name="MyAccount" component={MyAccountPage} />
      <AppStackNavigator.Screen name="Privacy" component={PrivacyPage} />
      <AppStackNavigator.Screen name="Security" component={SecurityPage} />
      <AppStackNavigator.Screen name="Settings" component={SettingsPage} />
    </AppStackNavigator.Navigator>
  );
}
