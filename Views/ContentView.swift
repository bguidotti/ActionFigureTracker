//
//  ContentView.swift
//  ActionFigureTracker
//
//  Main tab view - kid-friendly with big icons!
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var dataStore: FigureDataStore
    
    var body: some View {
        TabView {
            // All Figures
            FigureGridView()
                .tabItem {
                    Label("All Figures", systemImage: "figure.stand")
                }
            
            // My Collection (Have)
            FilteredFigureView(filterStatus: .have)
                .tabItem {
                    Label("I Have", systemImage: "checkmark.circle.fill")
                }
            
            // Wishlist (Want)
            FilteredFigureView(filterStatus: .want)
                .tabItem {
                    Label("I Want", systemImage: "star.fill")
                }
            
            // Stats & Fun
            StatsView()
                .tabItem {
                    Label("My Stats", systemImage: "chart.bar.fill")
                }
        }
        .tint(.purple) // Kid-friendly purple!
    }
}

#Preview {
    ContentView()
        .environmentObject(FigureDataStore())
}
