//
//  ActionFigureTrackerApp.swift
//  ActionFigureTracker
//
//  Main entry point for the Action Figure Tracker app
//

import SwiftUI

@main
struct ActionFigureTrackerApp: App {
    @StateObject private var dataStore = FigureDataStore()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(dataStore)
        }
    }
}
