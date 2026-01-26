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
    
    private let columns = [
        GridItem(.flexible(), spacing: 16),
        GridItem(.flexible(), spacing: 16)
    ]
    
    var filteredFigures: [ActionFigure] {
        dataStore.figures(for: selectedLine, status: filterStatus)
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
