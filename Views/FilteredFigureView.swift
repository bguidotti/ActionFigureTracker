//
//  FilteredFigureView.swift
//  ActionFigureTracker
//
//  Premium filtered view by status (Owned/Wishlist)
//

import SwiftUI

struct FilteredFigureView: View {
    @EnvironmentObject var dataStore: FigureDataStore
    let filterStatus: CollectionStatus
    @State private var selectedLine: FigureLine? = nil
    @State private var sortOption: SortOption = .newestFirst
    
    private let columns = [
        GridItem(.flexible(), spacing: 16)
    ]
    
    var filteredFigures: [ActionFigure] {
        let figures = dataStore.figures(for: selectedLine, status: filterStatus)
        return sortFigures(figures, by: sortOption)
    }
    
    private func sortFigures(_ figures: [ActionFigure], by option: SortOption) -> [ActionFigure] {
        switch option {
        case .newestFirst:
            return figures.sorted { $0.dateAdded < $1.dateAdded }
        case .oldestFirst:
            return figures.sorted { $0.dateAdded > $1.dateAdded }
        case .alphabetical:
            return figures.sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending }
        case .reverseAlphabetical:
            return figures.sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedDescending }
        }
    }
    
    var title: String {
        filterStatus == .have ? "Owned" : "Wishlist"
    }
    
    var emptyMessage: String {
        filterStatus == .have 
            ? "No figures in collection yet.\nBrowse and add figures you own."
            : "Your wishlist is empty.\nAdd figures you want to collect."
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                CollectorTheme.background
                    .ignoresSafeArea()
                
                VStack(spacing: 0) {
                    // Line Picker
                    LinePickerView(selectedLine: $selectedLine)
                        .padding(.horizontal)
                        .padding(.top, 8)
                    
                    if filteredFigures.isEmpty {
                        // Empty state
                        VStack(spacing: 16) {
                            Image(systemName: filterStatus == .have ? "checkmark.seal" : "sparkles")
                                .font(.system(size: 48))
                                .foregroundStyle(CollectorTheme.textSecondary.opacity(0.5))
                            
                            Text(filterStatus == .have ? "NO FIGURES YET" : "EMPTY WISHLIST")
                                .font(.system(.headline, design: .default, weight: .semibold))
                                .textCase(.uppercase)
                                .tracking(CollectorTheme.trackingWide)
                                .foregroundStyle(CollectorTheme.textSecondary)
                            
                            Text(emptyMessage)
                                .font(.subheadline)
                                .foregroundStyle(CollectorTheme.textSecondary.opacity(0.7))
                                .multilineTextAlignment(.center)
                        }
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else {
                        // Figure Grid
                        ScrollViewReader { proxy in
                            ScrollView {
                                // Count header
                                HStack {
                                    Text("\(filteredFigures.count) FIGURES")
                                        .font(.system(.caption, design: .monospaced, weight: .semibold))
                                        .textCase(.uppercase)
                                        .tracking(1)
                                        .foregroundStyle(CollectorTheme.textSecondary)
                                    Spacer()
                                }
                                .padding(.horizontal)
                                .padding(.top, 12)
                                .id("top")
                                
                                LazyVGrid(columns: columns, spacing: 16) {
                                    ForEach(filteredFigures) { figure in
                                        NavigationLink(destination: FigureDetailView(figure: figure)) {
                                            FigureCardView(figure: figure)
                                        }
                                        .buttonStyle(.plain)
                                        .id(figure.id)
                                    }
                                }
                                .padding()
                            }
                            .onChange(of: selectedLine) { _, _ in
                                withAnimation {
                                    proxy.scrollTo("top", anchor: .top)
                                }
                            }
                        }
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
                            .foregroundStyle(CollectorTheme.accentGold)
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
