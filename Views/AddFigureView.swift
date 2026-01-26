//
//  AddFigureView.swift
//  ActionFigureTracker
//
//  Add new figures - simple form for kids!
//

import SwiftUI

struct AddFigureView: View {
    @EnvironmentObject var dataStore: FigureDataStore
    @Environment(\.dismiss) var dismiss
    
    @State private var name = ""
    @State private var selectedLine: FigureLine = .dcMultiverse
    @State private var wave = ""
    @State private var status: CollectionStatus = .want
    @State private var notes = ""
    @State private var showingSuccess = false
    
    var isValid: Bool {
        !name.trimmingCharacters(in: .whitespaces).isEmpty
    }
    
    var body: some View {
        NavigationStack {
            Form {
                // Figure Name
                Section {
                    TextField("Figure Name", text: $name)
                        .font(.title3)
                } header: {
                    Label("What's the figure called?", systemImage: "person.fill")
                }
                
                // Figure Line
                Section {
                    Picker("Figure Line", selection: $selectedLine) {
                        ForEach(FigureLine.allCases) { line in
                            HStack {
                                Text(line.emoji)
                                Text(line.rawValue)
                            }
                            .tag(line)
                        }
                    }
                    .pickerStyle(.menu)
                } header: {
                    Label("Which toy line?", systemImage: "tag.fill")
                }
                
                // Wave (optional)
                Section {
                    TextField("Wave name (optional)", text: $wave)
                } header: {
                    Label("What wave is it from?", systemImage: "number")
                }
                
                // Status
                Section {
                    Picker("Status", selection: $status) {
                        ForEach(CollectionStatus.allCases, id: \.self) { status in
                            HStack {
                                Text(status.emoji)
                                Text(status.rawValue)
                            }
                            .tag(status)
                        }
                    }
                    .pickerStyle(.segmented)
                } header: {
                    Label("Do you have it?", systemImage: "questionmark.circle.fill")
                }
                
                // Notes
                Section {
                    TextField("Any notes?", text: $notes, axis: .vertical)
                        .lineLimit(3...6)
                } header: {
                    Label("Notes", systemImage: "pencil")
                }
                
                // Add Button
                Section {
                    Button(action: addFigure) {
                        HStack {
                            Spacer()
                            Label("Add Figure!", systemImage: "plus.circle.fill")
                                .font(.title3)
                                .fontWeight(.bold)
                            Spacer()
                        }
                    }
                    .disabled(!isValid)
                    .listRowBackground(isValid ? Color.green : Color.gray)
                    .foregroundStyle(.white)
                }
            }
            .navigationTitle("Add New Figure 🦸")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
            .overlay(
                // Success animation
                Group {
                    if showingSuccess {
                        VStack {
                            Image(systemName: "checkmark.circle.fill")
                                .font(.system(size: 80))
                                .foregroundStyle(.green)
                            Text("Added!")
                                .font(.title)
                                .fontWeight(.bold)
                        }
                        .padding(40)
                        .background(.ultraThinMaterial)
                        .clipShape(RoundedRectangle(cornerRadius: 24))
                        .transition(.scale.combined(with: .opacity))
                    }
                }
            )
        }
    }
    
    private func addFigure() {
        let newFigure = ActionFigure(
            name: name.trimmingCharacters(in: .whitespaces),
            line: selectedLine,
            wave: wave.isEmpty ? nil : wave,
            imageName: "placeholder", // User can add images later
            status: status,
            notes: notes
        )
        
        dataStore.addFigure(newFigure)
        
        // Show success animation
        withAnimation(.spring(response: 0.3)) {
            showingSuccess = true
        }
        
        // Dismiss after delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            dismiss()
        }
    }
}

#Preview {
    AddFigureView()
        .environmentObject(FigureDataStore())
}
