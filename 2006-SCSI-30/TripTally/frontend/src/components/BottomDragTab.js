// BottomDragTab.js
import React, { useRef, useEffect, useMemo } from 'react';
import {
  StyleSheet,
  Animated,
  PanResponder,
  Dimensions,
  View,
  Platform,
} from 'react-native';
import { useTheme } from '../context/ThemeContext';

const { height: SCREEN_HEIGHT } = Dimensions.get('window');

// Utility clamp
const clamp = (v, min, max) => Math.min(max, Math.max(min, v));

export default function BottomDragTab({
  children,
  maxHeight,          // e.g. 450 (if omitted, defaults to 70% screen)
  collapsedHeight = 60, // height visible when collapsed
  initialPosition,     // ✅ new optional prop for starting height (e.g. 200)
}) {
  const { theme } = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const FULL_EXPANDED = maxHeight || SCREEN_HEIGHT * 0.7;
  const MIN = 0; // fully expanded (top)
  const MAX = FULL_EXPANDED - collapsedHeight; // fully collapsed (bottom)

  // ✅ Compute starting position
  const START_Y = clamp(
    initialPosition !== undefined ? FULL_EXPANDED - initialPosition : MAX,
    MIN,
    MAX
  );

  // Animation refs
  const translateY = useRef(new Animated.Value(START_Y)).current;
  const dragStartY = useRef(START_Y);

  // Safety clamp
  const clampedTranslateY = Animated.diffClamp(translateY, MIN, MAX);

  // PanResponder for the drag handle only
  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: (_, g) => Math.abs(g.dy) > 5,

      onPanResponderGrant: () => {
        translateY.stopAnimation(current => {
          dragStartY.current = clamp(current, MIN, MAX);
          translateY.setValue(dragStartY.current);
        });
      },

      onPanResponderMove: (_, g) => {
        const newPos = clamp(dragStartY.current + g.dy, MIN, MAX);
        translateY.setValue(newPos);
      },

      onPanResponderRelease: (_, g) => {
        const MOMENTUM = 80;
        const projected = dragStartY.current + g.dy + g.vy * MOMENTUM;
        const finalY = clamp(projected, MIN, MAX);

        Animated.timing(translateY, {
          toValue: finalY,
          duration: 160,
          useNativeDriver: true,
        }).start(() => {
          dragStartY.current = finalY;
          translateY.setValue(finalY);
        });
      },
    })
  ).current;

  // ✅ Ensure we start at the chosen position
  useEffect(() => {
    translateY.setValue(START_Y);
    dragStartY.current = START_Y;
  }, [START_Y]);

  return (
    <Animated.View
      style={[
        styles.bottomSheet,
        {
          height: FULL_EXPANDED,
          transform: [{ translateY: clampedTranslateY }],
        },
      ]}
    >
      <View style={styles.innerContainer}>
        {/* Drag handle area - only this part responds to drag gestures */}
        <View {...panResponder.panHandlers} style={styles.dragHandleArea}>
          <View style={styles.handleBar} />
        </View>
        {/* Content area - allows free scrolling */}
        <View style={styles.contentArea}>
          {children}
        </View>
      </View>
    </Animated.View>
  );
}

const createStyles = (theme) =>
  StyleSheet.create({
    bottomSheet: {
      position: 'absolute',
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'transparent',
    },
    innerContainer: {
      flex: 1,
      backgroundColor: theme.colors.card,
      borderTopLeftRadius: 24,
      borderTopRightRadius: 24,
      shadowColor: '#000',
      shadowOpacity: theme.mode === 'dark' ? 0.4 : 0.15,
      shadowRadius: 12,
      elevation: 10,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.colors.border,
    },
    dragHandleArea: {
      paddingHorizontal: 20,
      paddingTop: 16,
      paddingBottom: 8,
      alignItems: 'center',
    },
    handleBar: {
      width: 50,
      height: 5,
      borderRadius: 3,
      backgroundColor: theme.colors.pill,
    },
    contentArea: {
      flex: 1,
      paddingHorizontal: 20,
      paddingBottom: Platform.OS === 'ios' ? 34 : 16,
    },
  });
