//
//  FigureDataStore.swift
//  ActionFigureTracker
//
//  Manages all figure data with persistence
//

import Foundation
import SwiftUI
import Combine

class FigureDataStore: ObservableObject {
    @Published var figures: [ActionFigure] = []
    
    private let saveKey = "SavedFigures"
    
    init() {
            loadFigures()
            
            // If no saved data, load from the JSON file
            if figures.isEmpty {
                figures = DataLoader.loadFigures() // <--- CHANGED THIS LINE
                saveFigures()
            }
        }
    
    // MARK: - Filtering
    
    func figures(for line: FigureLine?) -> [ActionFigure] {
        guard let line = line else { return figures }
        return figures.filter { $0.line == line }
    }
    
    func figures(with status: CollectionStatus) -> [ActionFigure] {
        figures.filter { $0.status == status }
    }
    
    func figures(for line: FigureLine?, status: CollectionStatus?) -> [ActionFigure] {
        var result = figures
        
        if let line = line {
            result = result.filter { $0.line == line }
        }
        
        if let status = status {
            result = result.filter { $0.status == status }
        }
        
        return result.sorted { $0.name < $1.name }
    }
    
    func favorites() -> [ActionFigure] {
        figures.filter { $0.isFavorite }
    }
    
    // MARK: - Counts
    
    func count(for line: FigureLine, status: CollectionStatus) -> Int {
        figures.filter { $0.line == line && $0.status == status }.count
    }
    
    var totalHave: Int {
        figures.filter { $0.status == .have }.count
    }
    
    var totalWant: Int {
        figures.filter { $0.status == .want }.count
    }
    
    // MARK: - Actions
    
    func toggleStatus(for figure: ActionFigure) {
        if let index = figures.firstIndex(where: { $0.id == figure.id }) {
            figures[index].status = figures[index].status == .have ? .want : .have
            saveFigures()
        }
    }
    
    func toggleFavorite(for figure: ActionFigure) {
        if let index = figures.firstIndex(where: { $0.id == figure.id }) {
            figures[index].isFavorite.toggle()
            saveFigures()
        }
    }
    
    func updateNotes(for figure: ActionFigure, notes: String) {
        if let index = figures.firstIndex(where: { $0.id == figure.id }) {
            figures[index].notes = notes
            saveFigures()
        }
    }
    
    func addFigure(_ figure: ActionFigure) {
        figures.append(figure)
        saveFigures()
    }
    
    func deleteFigure(_ figure: ActionFigure) {
        figures.removeAll { $0.id == figure.id }
        saveFigures()
    }
    
    // MARK: - Persistence
    
    private func saveFigures() {
        if let encoded = try? JSONEncoder().encode(figures) {
            UserDefaults.standard.set(encoded, forKey: saveKey)
        }
    }
    
    private func loadFigures() {
        if let data = UserDefaults.standard.data(forKey: saveKey),
           let decoded = try? JSONDecoder().decode([ActionFigure].self, from: data) {
            figures = decoded
        }
    }
    
    /// Reset to mock data (useful for testing)
    /// Reset to data from JSON file
    func resetToMockData() {
        figures = DataLoader.loadFigures() // <--- CHANGED THIS LINE
        saveFigures()
    }
}
