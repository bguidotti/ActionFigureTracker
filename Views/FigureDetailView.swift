//
//  FigureDetailView.swift
//  ActionFigureTracker
//
//  Detailed view of a single figure - big image, big buttons!
//

import SwiftUI

struct FigureDetailView: View {
    @EnvironmentObject var dataStore: FigureDataStore
    @Environment(\.dismiss) var dismiss
    
    let figure: ActionFigure
    @State private var notes: String = ""
    @State private var showingConfetti = false
    @State private var showingDeleteAlert = false
    
    // Get the current figure from dataStore for live updates
    var currentFigure: ActionFigure {
        dataStore.figures.first { $0.id == figure.id } ?? figure
    }
    
    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Big Image
                ZStack(alignment: .topTrailing) {
                    // Background
                    RoundedRectangle(cornerRadius: 24)
                        .fill(Color.gray.opacity(0.1))
                        .frame(minHeight: 400)
                    
                    FigureImageView(imageName: currentFigure.imageName)
                        .frame(maxWidth: .infinity)
                        .frame(minHeight: 400)
                        .clipShape(RoundedRectangle(cornerRadius: 24))
                        .shadow(color: .black.opacity(0.2), radius: 10, x: 0, y: 5)
                    
                    // Badges overlay
                    VStack(alignment: .trailing, spacing: 8) {
                        // Platinum badge
                        if currentFigure.isPlatinum {
                            PlatinumBadge()
                        }
                        // Favorite button
                        Button(action: {
                            withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) {
                                dataStore.toggleFavorite(for: figure)
                            }
                        }) {
                            Image(systemName: currentFigure.isFavorite ? "heart.fill" : "heart")
                                .font(.title)
                                .foregroundStyle(currentFigure.isFavorite ? .red : .gray)
                                .padding(16)
                                .background(.ultraThinMaterial)
                                .clipShape(Circle())
                        }
                    }
                    .padding()
                }
                
                // Name and Line
                VStack(spacing: 8) {
                    VStack(spacing: 4) {
                        Text(currentFigure.name)
                            .font(.largeTitle)
                            .fontWeight(.bold)
                            .multilineTextAlignment(.center)
                        
                        if currentFigure.isPlatinum {
                            PlatinumBadge()
                        }
                    }
                    
                    HStack {
                        Text(currentFigure.line.emoji)
                        Text(currentFigure.line.rawValue)
                            .font(.title3)
                            .foregroundStyle(.secondary)
                    }
                    
                    if let wave = currentFigure.wave {
                        Text("Wave: \(wave)")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                }
                
                // BIG Status Button
                Button(action: {
                    withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) {
                        if currentFigure.status == .want {
                            showingConfetti = true
                            DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                                showingConfetti = false
                            }
                        }
                        dataStore.toggleStatus(for: figure)
                    }
                }) {
                    HStack(spacing: 12) {
                        Image(systemName: currentFigure.status == .have ? "checkmark.circle.fill" : "star.fill")
                            .font(.title)
                        Text(currentFigure.status == .have ? "I HAVE IT! ✅" : "I WANT IT! ⭐")
                            .font(.title2)
                            .fontWeight(.bold)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 20)
                    .background(currentFigure.status == .have ? Color.green : Color.orange)
                    .foregroundStyle(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 20))
                }
                .scaleEffect(showingConfetti ? 1.1 : 1.0)
                .animation(.spring(response: 0.3), value: showingConfetti)
                
                // Notes Section
                VStack(alignment: .leading, spacing: 12) {
                    Text("My Notes 📝")
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    TextEditor(text: $notes)
                        .frame(minHeight: 100)
                        .padding(12)
                        .background(Color(.systemGray6))
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                        .onChange(of: notes) { _, newValue in
                            dataStore.updateNotes(for: figure, notes: newValue)
                        }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                
                Spacer(minLength: 50)
            }
            .padding()
        }
        .overlay(
            ConfettiView(isShowing: showingConfetti)
        )
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button(role: .destructive) {
                    showingDeleteAlert = true
                } label: {
                    Image(systemName: "trash")
                        .foregroundStyle(.red)
                }
            }
        }
        .alert("Delete Figure?", isPresented: $showingDeleteAlert) {
            Button("Cancel", role: .cancel) { }
            Button("Delete", role: .destructive) {
                dataStore.deleteFigure(figure)
                dismiss()
            }
        } message: {
            Text("Are you sure you want to remove \(currentFigure.name) from your collection?")
        }
        .onAppear {
            notes = currentFigure.notes
        }
    }
}

#Preview {
    NavigationStack {
        FigureDetailView(figure: MockData.dcMultiverseFigures[0])
            .environmentObject(FigureDataStore())
    }
}
