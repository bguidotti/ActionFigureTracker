//
//  FilteredFigureView.swift
//  ActionFigureTracker
//
//  Shows figures filtered by status (Have/Want)
//

import SwiftUI

struct FilteredFigureView: View {
    @EnvironmentObject var dataStore: FigureDataStore
    let filterStatus: CollectionStatus
    @State private var selectedLine: FigureLine? = nil
    @State private var sortOption: SortOption = .newestFirst
    
    private let columns = [
        GridItem(.flexible(), spacing: 16),
        GridItem(.flexible(), spacing: 16)
    ]
    
    var filteredFigures: [ActionFigure] {
        let figures = dataStore.figures(for: selectedLine, status: filterStatus)
        return sortFigures(figures, by: sortOption)
    }
    
    private func sortFigures(_ figures: [ActionFigure], by option: SortOption) -> [ActionFigure] {
        switch option {
        case .newestFirst:
            return figures.sorted { $0.dateAdded > $1.dateAdded }
        case .oldestFirst:
            return figures.sorted { $0.dateAdded < $1.dateAdded }
        case .alphabetical:
            return figures.sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending }
        case .reverseAlphabetical:
            return figures.sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedDescending }
        }
    }
    
    var title: String {
        filterStatus == .have ? "My Collection! 🏆" : "My Wishlist! ⭐"
    }
    
    var emptyMessage: String {
        filterStatus == .have 
            ? "No figures yet!\nTap the star on figures you have!"
            : "Your wishlist is empty!\nAdd figures you want!"
    }
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Line Picker
                LinePickerView(selectedLine: $selectedLine)
                    .padding(.horizontal)
                    .padding(.top, 8)
                
                if filteredFigures.isEmpty {
                    // Empty state
                    ContentUnavailableView {
                        Label(filterStatus == .have ? "No Figures Yet" : "Empty Wishlist", 
                              systemImage: filterStatus == .have ? "figure.stand" : "star")
                    } description: {
                        Text(emptyMessage)
                    }
                } else {
                    // Figure Grid
                    ScrollView {
                        // Count header
                        HStack {
                            Text("\(filteredFigures.count) figures")
                                .font(.headline)
                                .foregroundStyle(.secondary)
                            Spacer()
                        }
                        .padding(.horizontal)
                        .padding(.top, 8)
                        
                        LazyVGrid(columns: columns, spacing: 20) {
                            ForEach(filteredFigures) { figure in
                                NavigationLink(destination: FigureDetailView(figure: figure)) {
                                    FigureCardView(figure: figure)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                        .padding()
                    }
                }
            }
            .navigationTitle(title)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        Picker("Sort", selection: $sortOption) {
                            ForEach(SortOption.allCases, id: \.self) { option in
                                Label(option.rawValue, systemImage: option.icon)
                                    .tag(option)
                            }
                        }
                    } label: {
                        Image(systemName: "arrow.up.arrow.down.circle")
                            .font(.title2)
                            .foregroundStyle(.purple)
                    }
                }
            }
        }
    }
}

#Preview("Have") {
    FilteredFigureView(filterStatus: .have)
        .environmentObject(FigureDataStore())
}

#Preview("Want") {
    FilteredFigureView(filterStatus: .want)
        .environmentObject(FigureDataStore())
}
