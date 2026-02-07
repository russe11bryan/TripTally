// A corrected version of the metrics fetching code
useEffect(() => {
  const fetchAll = async () => {
    if (!origin || !destination) return;
    const modes = ["driving", "transit", "walking", "bicycling"];
    const next = {};

    try {
      await Promise.all(
        modes.map(async (m) => {
          try {
            // Get route details
            const routeUrl =
              `${API_BASE}/maps/directions?origin=${origin.latitude},${origin.longitude}` +
              `&destination=${destination.latitude},${destination.longitude}&mode=${m}`;
            const routeRes = await fetch(routeUrl, { headers: { Accept: "application/json" } });
            if (!routeRes.ok) throw new Error(`HTTP ${routeRes.status}`);
            const routeData = await routeRes.json();
            const { duration, distance } = parseDirections(routeData);
            
            if (m === "driving" || m === "transit") {
              try {
                const distanceKm = parseFloat((distance || "").replace(/[^\d.]/g, "")) || 0;
                const polyline = routeData?.routes?.[0]?.overview_polyline?.points || 
                               routeData?.routes?.[0]?.encoded_polyline ||
                               routeData?.overview_polyline?.points || "";
                
                const metricsUrl = `${API_BASE}/metrics/compare?` +
                  `distance_km=${distanceKm}&` +
                  `route_polyline=${encodeURIComponent(polyline)}&` +
                  `origin=${origin.latitude},${origin.longitude}&` +
                  `destination=${destination.latitude},${destination.longitude}&` +
                  `fare_category=adult_card_fare`;
                
                console.log('Fetching metrics:', metricsUrl);
                const metricsRes = await fetch(metricsUrl);
                const metricsText = await metricsRes.text();
                
                if (!metricsRes.ok) {
                  console.error('Metrics API error:', metricsText);
                  throw new Error(`HTTP ${metricsRes.status}: ${metricsText}`);
                }
                
                let metricsData;
                try {
                  metricsData = JSON.parse(metricsText);
                  console.log('Metrics response:', JSON.stringify(metricsData, null, 2));
                } catch (e) {
                  console.error('Failed to parse metrics response:', metricsText);
                  throw new Error('Invalid JSON response from metrics API');
                }

                if (m === "driving" && metricsData?.driving) {
                  const driving = metricsData.driving;
                  next[m] = {
                    time: duration || "--",
                    distance: distance || "--",
                    cost: driving.total_cost != null ? `$${driving.total_cost.toFixed(2)}` : "--",
                    co2: driving.co2_emissions_kg != null ? `${driving.co2_emissions_kg.toFixed(2)} kg` : "--",
                    fuel_cost: driving.fuel_cost_sgd != null ? `$${driving.fuel_cost_sgd.toFixed(2)}` : "--",
                    erp_charges: driving.erp_charges != null ? `$${driving.erp_charges.toFixed(2)}` : "--"
                  };
                } else if (m === "transit" && metricsData?.public_transport) {
                  const pt = metricsData.public_transport;
                  const mrtFare = pt.mrt_fare != null ? parseFloat(pt.mrt_fare) : null;
                  const busFare = pt.bus_fare != null ? parseFloat(pt.bus_fare) : null;
                  const totalFare = (mrtFare != null && busFare != null) ? 
                    (mrtFare + busFare).toFixed(2) : null;
                  
                  next[m] = {
                    time: duration || "--",
                    distance: distance || "--",
                    cost: totalFare != null ? `$${totalFare}` : "--",
                    co2: "0 kg",  // Public transport CO2 emissions considered negligible per passenger
                    mrt_fare: mrtFare != null ? `$${mrtFare.toFixed(2)}` : "--",
                    bus_fare: busFare != null ? `$${busFare.toFixed(2)}` : "--"
                  };
                }
              } catch (metricsError) {
                console.error("Metrics fetch error:", metricsError);
                next[m] = {
                  time: duration || "--",
                  distance: distance || "--",
                  cost: "--",
                  co2: "--"
                };
              }
            } else {
              // For walking and cycling, just use route data
              next[m] = {
                time: duration || "--",
                distance: distance || "--",
                cost: "Free",
                co2: "0 kg"
              };
            }
          } catch (error) {
            console.error(`Error fetching ${m} route:`, error);
            next[m] = {
              time: "--",
              distance: "--",
              cost: "--",
              co2: "--"
            };
          }
        })
      );
      setMetrics(next);
    } catch (error) {
      console.error("Error in fetchAll:", error);
    }
  };
  fetchAll();
}, [origin, destination]);