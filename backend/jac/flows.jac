 
# // WASTELINK ROUTING WALKER
# // Handles all routing logic for the system
# // ============================================

walker WasteLinkRouter {
    has user_id: str;
    has role: str; # "user", "collector", "admin"
    has action: str; #"login", "schedule_pickup", "optimize_route", etc.
    has data: dict = {};
    
    # // Entry point - starts at root
    can route with entry {
        # // Create nodes if they don't exist
        alice = root ++> User(name="Alice");
        bob = root ++> User(name="Bob");
        req1 = root ++> Request(id=101);
        
        # // Show visited log
        print(f"Visited locations: {router.visited}");
        
        # // Route based on action
        if (action == "login") {
            visit ::handle_login();
        } elif (action == "schedule_pickup") {
            visit ::handle_schedule_pickup();
        } elif (action == "optimize_route") {
            visit ::handle_optimize_route();
        } elif (action == "get_dashboard") {
            visit ::handle_dashboard();
        } else {
            report {"error": "Unknown action"};
        }
    }
    
    # // ========================================
    # // LOGIN HANDLER
    # // ========================================
    can handle_login {
        # // Find user by ID
        user_node = -[user_id]-> (:Person:);
        
        if (!user_node) {
            report {"success": false, "error": "User not found"};
            disengage;
        }
        
        # // Check roles
        roles = user_node.roles;
        
        if (role not in roles) {
            report {"success": false, "error": "Unauthorized role"};
            disengage;
        }
        
        # // Build role-specific data
        role_data = {};
        
        if ("collector" in roles) {
            # // Get collector's pending pickups
            collector_edge = user_node -[acts_as_collector]-> ();
            pending_pickups = user_node <-[assigned_to]- (:Pickup:)[status == "assigned"];
            
            role_data["collector"] = {
                "status": collector_edge.status,
                "earnings_today": collector_edge.earnings_today,
                "pending_pickups": pending_pickups.length,
                "rating": collector_edge.rating
            };
        }
        
        if ("user" in roles) {
            user_edge = user_node -[acts_as_user]-> ();
            scheduled_pickups = user_node -[schedules]-> (:Pickup:)[status in ["pending", "assigned"]];
            
            role_data["user"] = {
                "total_pickups": user_edge.total_pickups_scheduled,
                "is_premium": user_edge.premium_status,
                "scheduled_pickups": scheduled_pickups.length
            };
        }
        
        if ("admin" in roles) {
            admin_edge = user_node -[acts_as_company]-> ();
            company = Company(id == admin_edge.company_id);
            
            role_data["admin"] = {
                "company_name": company.name,
                "active_collectors": company.active_collectors,
                "pickups_today": company.pickups_this_month
            };
        }
        
        report {
            "success": true,
            "user": {
                "id": user_node.id,
                "name": user_node.name,
                "email": user_node.email,
                "roles": roles
            },
            "role_data": role_data
        };
    }
    
    # // ========================================
    # // SCHEDULE PICKUP HANDLER
    # // ========================================
    can handle_schedule_pickup {
        # // Get user node
        user_node = Person(id == user_id);
        
        if (!user_node) {
            report {"success": false, "error": "User not found"};
            disengage;
        }
        
        # // Extract pickup data
        location = data["location"];
        waste_types = data["waste_types"];
        scheduled_time = data["scheduled_time"];
        
        # // Create Location node (if doesn't exist)
        location_node = Location(
            lat == location["lat"],
            lng == location["lng"]
        );
        
        if (!location_node) {
            location_node = spawn Location(
                address = location["address"],
                lat = location["lat"],
                lng = location["lng"],
                zone = ::calculate_zone(location)
            );
        }
        
        # // Create Pickup node
        new_pickup = spawn Pickup(
            id = ::generate_uuid(),
            status = "pending",
            estimated_weight_kg = data["estimated_weight"],
            location = location,
            address = location["address"],
            scheduled_time = scheduled_time,
            payment_amount = 300.0, # KES 300
            special_instructions = data.get("instructions", ""),
            created_at = ::timestamp()
        );
        
        # // Link user to pickup
        user_node -[schedules(scheduled_at=::timestamp())]-> new_pickup;
        
        # // Link pickup to location
        new_pickup -[located_at]-> location_node;
        
        # // Link waste types
        for waste_type_name in waste_types {
            waste_node = WasteType(name == waste_type_name);
            
            if (!waste_node) {
                # // Create waste type
                waste_node = spawn WasteType(
                    name = waste_type_name,
                    category = "recyclable",# Default
                    value_per_kg = 0.40,
                    co2_saved_per_kg = 1.5
                );
            }
            
            new_pickup -[contains_waste(quantity_kg=5.0)]-> waste_node;
        }
        
        # // Trigger auto-assignment
        matcher = spawn PickupMatcher(pickup_id=new_pickup.id);
        assignment_result = matcher.match();
        
        report {
            "success": true,
            "pickup_id": new_pickup.id,
            "status": new_pickup.status,
            "scheduled_time": scheduled_time,
            "assigned_collector": assignment_result.get("collector_name", "Pending")
        };
    }
    
    # // ========================================
    # // ROUTE OPTIMIZATION HANDLER
    # // ========================================
    can handle_optimize_route {
        # // Get collector node
        collector_node = Person(id == user_id);
        
        if (!collector_node) {
            report {"success": false, "error": "Collector not found"};
            disengage;
        }
        
        # // Get assigned pickups
        assigned_pickups = collector_node <-[assigned_to]- (:Pickup:)[status == "assigned"];
        
        if (assigned_pickups.length == 0) {
            report {"success": false, "message": "No pickups to optimize"};
            disengage;
        }
        
        # // Build pickup list for optimization
        pickup_points = [];
        for pickup in assigned_pickups {
            location = pickup -[located_at]-> (:Location:);
            pickup_points.append({
                "id": pickup.id,
                "lat": location.lat,
                "lng": location.lng,
                "weight_kg": pickup.estimated_weight_kg,
                "address": pickup.address
            });
        }
        
        # // Call optimization algorithm
        collector_edge = collector_node -[acts_as_collector]-> ();
        current_location = collector_node.current_location;
        
        optimized = ::optimize_tsp_route(
            start = current_location,
            points = pickup_points,
            capacity = collector_edge.capacity_kg
        );
        
        # // Create Route node
        route_node = spawn Route(
            id = ::generate_uuid(),
            created_at = ::timestamp(),
            status = "planned",
            pickup_ids = [p["id"] for p in pickup_points],
            optimized_sequence = optimized["sequence"],
            total_distance_km = optimized["distance"],
            total_duration_min = optimized["duration"],
            estimated_fuel_cost = optimized["fuel_cost"],
            estimated_co2_kg = optimized["co2"],
            time_saved_min = optimized["time_saved"],
            fuel_saved_usd = optimized["fuel_saved"],
            map_polyline = optimized["polyline"]
        );
        
        # // Link collector to route
        collector_node -[follows_route(started_at=::timestamp())]-> route_node;
        
        report {
            "success": true,
            "route_id": route_node.id,
            "total_pickups": pickup_points.length,
            "optimized_sequence": optimized["sequence"],
            "total_distance_km": optimized["distance"],
            "estimated_duration_min": optimized["duration"],
            "savings": {
                "time_saved_min": optimized["time_saved"],
                "fuel_saved_ksh": optimized["fuel_saved"] * 150, #Convert to KES
                "efficiency_gain": optimized["efficiency_percent"]
            },
            "map_polyline": optimized["polyline"],
            "directions": optimized["directions"]
        };
    }
    
    # // ========================================
    # // DASHBOARD DATA HANDLER
    # // ========================================
    can handle_dashboard {
        person = Person(id == user_id);
        
        if (!person) {
            report {"success": false, "error": "User not found"};
            disengage;
        }
        
        dashboard_data = {};
        
        # // Collector Dashboard
        if (role == "collector") {
            collector_edge = person -[acts_as_collector]-> ();
            todays_pickups = person <-[assigned_to]- (:Pickup:)[status in ["assigned", "in_progress"]];
            completed_today = person <-[assigned_to]- (:Pickup:)[status == "completed"];
            
            dashboard_data = {
                "collector": {
                    "name": person.name,
                    "status": collector_edge.status,
                    "rating": collector_edge.rating,
                    "earnings": {
                        "today": collector_edge.earnings_today,
                        "week": collector_edge.earnings_week,
                        "month": collector_edge.earnings_month
                    },
                    "pickups": {
                        "pending": todays_pickups.length,
                        "completed_today": completed_today.length,
                        "total": collector_edge.total_pickups_completed
                    },
                    "performance": {
                        "on_time_rate": collector_edge.on_time_rate,
                        "completion_rate": collector_edge.completion_rate,
                        "customer_satisfaction": collector_edge.customer_satisfaction
                    }
                }
            };
        }
        
        # // User Dashboard
        elif (role == "user") {
            user_edge = person -[acts_as_user]-> ();
            scheduled = person -[schedules]-> (:Pickup:)[status in ["pending", "assigned", "in_progress"]];
            history = person -[schedules]-> (:Pickup:)[status == "completed"];
            
            dashboard_data = {
                "user": {
                    "name": person.name,
                    "is_premium": user_edge.premium_status,
                    "total_pickups": user_edge.total_pickups_scheduled,
                    "scheduled_pickups": scheduled.length,
                    "pickup_history": history.length,
                    "environmental_impact": {
                        "total_waste_kg": ::sum([p.actual_weight_kg for p in history]),
                        "co2_saved_kg": ::calculate_co2_saved(history),
                        "recycling_rate": ::calculate_recycling_rate(history)
                    }
                }
            };
        }
        
        # // Admin Dashboard
        elif (role == "admin") {
            admin_edge = person -[acts_as_company]-> ();
            company = Company(id == admin_edge.company_id);
            
            collectors = Person -[employed_by]-> company[is_active == true];
            todays_pickups = company -[manages]-> (:Pickup:)[
                status == "completed" and 
                ::is_today(completed_time)
            ];
            
            dashboard_data = {
                "company": {
                    "name": company.name,
                    "plan": company.plan,
                    "active_collectors": collectors.length,
                    "today_stats": {
                        "pickups_completed": todays_pickups.length,
                        "waste_collected_kg": ::sum([p.actual_weight_kg for p in todays_pickups]),
                        "revenue": company.pickups_this_month * 300,
                        "collector_earnings": ::sum([c.earnings_today for c in collectors])
                    },
                    "month_stats": {
                        "total_pickups": company.pickups_this_month,
                        "total_waste_kg": company.total_waste_collected_kg,
                        "recycling_rate": ::calculate_company_recycling_rate(company)
                    }
                }
            };
        }
        
        report {
            "success": true,
            "dashboard": dashboard_data
        };
    }
}

# // ============================================
# // PICKUP MATCHER WALKER
# // Assigns pickups to best available collector
# // ============================================

walker PickupMatcher {
    has pickup_id: str;
    
    can match with Pickup entry {
        # // Get pickup location
        pickup_location = here -[located_at]-> (:Location:);
        
        # // Find available collectors
        available_collectors = [];
        
        all_collectors = Person[roles contains "collector"];
        
        for collector in all_collectors {
            collector_edge = collector -[acts_as_collector]-> ();
            
            if (collector_edge.status == "active") {
                # // Calculate distance
                collector_loc = collector.current_location;
                distance = ::calculate_distance(
                    pickup_location.lat, 
                    pickup_location.lng,
                    collector_loc["lat"],
                    collector_loc["lng"]
                );
                
                # // Check capacity
                can_carry = (collector_edge.capacity_kg - collector_edge.current_load_kg) >= here.estimated_weight_kg;
                
                if (distance <= 5.0 and can_carry) {
                    score = ::calculate_match_score(
                        distance = distance,
                        rating = collector_edge.rating,
                        current_load = collector_edge.current_load_kg,
                        capacity = collector_edge.capacity_kg
                    );
                    
                    available_collectors.append({
                        "collector": collector,
                        "distance": distance,
                        "score": score
                    });
                }
            }
        }
        
        if (available_collectors.length == 0) {
            report {"success": false, "message": "No available collectors"};
            disengage;
        }
        
        # // Sort by score (highest first)
        available_collectors = ::sort_by_key(available_collectors, "score", reverse=true);
        
        # // Assign to best match
        best = available_collectors[0];
        best_collector = best["collector"];
        
        # // Create assignment
        best_collector -[assigned_to(
            assigned_at = ::timestamp(),
            auto_assigned = true,
            distance_to_pickup_km = best["distance"]
        )]-> here;
        
        # // Update pickup status
        here.status = "assigned";
        
        # // Update collector load
        collector_edge = best_collector -[acts_as_collector]-> ();
        collector_edge.current_load_kg += here.estimated_weight_kg;
        
        # // Send notification
        ::send_notification(
            user_id = best_collector.id,
            message = f"New pickup assigned at {here.address}",
            type = "new_pickup"
        );
        
        report {
            "success": true,
            "collector_id": best_collector.id,
            "collector_name": best_collector.name,
            "distance_km": best["distance"],
            "eta_minutes": ::calculate_eta(best["distance"])
        };
    }
}
