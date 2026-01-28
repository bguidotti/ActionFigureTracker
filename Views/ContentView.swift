//
//  ContentView.swift
//  ActionFigureTracker
//
//  Main tab view - Premium collector's dashboard
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var dataStore: FigureDataStore
    
    init() {
        // Configure TabBar appearance for glassmorphism effect
        let tabBarAppearance = UITabBarAppearance()
        tabBarAppearance.configureWithTransparentBackground()
        tabBarAppearance.backgroundEffect = UIBlurEffect(style: .systemUltraThinMaterialDark)
        tabBarAppearance.backgroundColor = UIColor(CollectorTheme.cardBackground.opacity(0.5))
        
        // Selected item styling
        tabBarAppearance.stackedLayoutAppearance.selected.iconColor = UIColor(CollectorTheme.accentGold)
        tabBarAppearance.stackedLayoutAppearance.selected.titleTextAttributes = [
            .foregroundColor: UIColor(CollectorTheme.accentGold)
        ]
        
        // Normal item styling
        tabBarAppearance.stackedLayoutAppearance.normal.iconColor = UIColor(CollectorTheme.textSecondary)
        tabBarAppearance.stackedLayoutAppearance.normal.titleTextAttributes = [
            .foregroundColor: UIColor(CollectorTheme.textSecondary)
        ]
        
        UITabBar.appearance().standardAppearance = tabBarAppearance
        UITabBar.appearance().scrollEdgeAppearance = tabBarAppearance
        
        // Configure NavigationBar appearance for glassmorphism
        let navBarAppearance = UINavigationBarAppearance()
        navBarAppearance.configureWithTransparentBackground()
        navBarAppearance.backgroundEffect = UIBlurEffect(style: .systemUltraThinMaterialDark)
        navBarAppearance.backgroundColor = UIColor(CollectorTheme.cardBackground.opacity(0.5))
        navBarAppearance.titleTextAttributes = [
            .foregroundColor: UIColor(CollectorTheme.textPrimary)
        ]
        navBarAppearance.largeTitleTextAttributes = [
            .foregroundColor: UIColor(CollectorTheme.textPrimary)
        ]
        
        UINavigationBar.appearance().standardAppearance = navBarAppearance
        UINavigationBar.appearance().scrollEdgeAppearance = navBarAppearance
        UINavigationBar.appearance().compactAppearance = navBarAppearance
    }
    
    var body: some View {
        TabView {
            // All Figures
            FigureGridView()
                .tabItem {
                    Label("Collection", systemImage: "square.grid.2x2.fill")
                }
            
            // My Collection (Have)
            FilteredFigureView(filterStatus: .have)
                .tabItem {
                    Label("Owned", systemImage: "checkmark.seal.fill")
                }
            
            // Wishlist (Want)
            FilteredFigureView(filterStatus: .want)
                .tabItem {
                    Label("Wishlist", systemImage: "sparkles")
                }
            
            // Stats & Fun
            StatsView()
                .tabItem {
                    Label("Analytics", systemImage: "chart.bar.fill")
                }
        }
        .tint(CollectorTheme.accentGold)
        .preferredColorScheme(.dark)
    }
}

#Preview {
    ContentView()
        .environmentObject(FigureDataStore())
}
