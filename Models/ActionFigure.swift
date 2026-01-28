//
//  ActionFigure.swift
//  ActionFigureTracker
//
//  Data model for action figures
//

import Foundation

/// The different action figure lines your son collects
enum FigureLine: String, CaseIterable, Codable, Identifiable {
    // DC Lines
    case dcMultiverse = "DC Multiverse"
    case dcSuperPowers = "DC Super Powers"
    case dcRetro = "DC Retro"
    case dcDirect = "DC Direct"
    
    // Masters of the Universe (split into sub-lines)
    case motuOrigins = "MOTU Origins"
    case motuMasterverse = "MOTU Masterverse"
    
    // Marvel
    case marvelLegends = "Marvel Legends"
    
    // Star Wars
    case starWarsBlackSeries = "Star Wars Black Series"
    
    var id: String { rawValue }
    
    /// Fun emoji for each line
    var emoji: String {
        switch self {
        case .dcMultiverse: return "🦇"
        case .dcSuperPowers: return "💪"
        case .dcRetro: return "📼"
        case .dcDirect: return "🎯"
        case .motuOrigins: return "⚔️"
        case .motuMasterverse: return "👑"
        case .marvelLegends: return "🕷️"
        case .starWarsBlackSeries: return "⭐"
        }
    }
    
    /// Brand color for each line
    var colorName: String {
        switch self {
        case .dcMultiverse: return "DCBlue"
        case .dcSuperPowers: return "DCPower"
        case .dcRetro: return "DCRetro"
        case .dcDirect: return "DCDirect"
        case .motuOrigins: return "MOTUOrigins"
        case .motuMasterverse: return "MOTUMasterverse"
        case .marvelLegends: return "MarvelRed"
        case .starWarsBlackSeries: return "StarWars"
        }
    }
}

/// Collection status - simple for kids!
enum CollectionStatus: String, Codable, CaseIterable {
    case want = "I Want It!"
    case have = "I Have It!"
    
    var emoji: String {
        switch self {
        case .want: return "⭐"
        case .have: return "✅"
        }
    }
}

/// Sort options for figure lists
enum SortOption: String, CaseIterable {
    case newestFirst = "Newest First"
    case oldestFirst = "Oldest First"
    case alphabetical = "A-Z"
    case reverseAlphabetical = "Z-A"
    
    var icon: String {
        switch self {
        case .newestFirst: return "arrow.down.circle"
        case .oldestFirst: return "arrow.up.circle"
        case .alphabetical: return "textformat.abc"
        case .reverseAlphabetical: return "textformat.abc.dottedunderline"
        }
    }
}

/// Main action figure model
struct ActionFigure: Identifiable, Codable {
    let id: UUID
    var name: String
    var line: FigureLine
    var wave: String?           // e.g., "Wave 1", "BAF Bane Wave"
    var imageName: String       // Name of image in Assets
    var status: CollectionStatus
    var notes: String
    var isFavorite: Bool
    var dateAdded: Date
    var year: Int?              // Year from CSV - used for proper sorting
    
    init(
        id: UUID = UUID(),
        name: String,
        line: FigureLine,
        wave: String? = nil,
        imageName: String,
        status: CollectionStatus = .want,
        notes: String = "",
        isFavorite: Bool = false,
        dateAdded: Date = Date(),
        year: Int? = nil
    ) {
        self.id = id
        self.name = name
        self.line = line
        self.wave = wave
        self.imageName = imageName
        self.status = status
        self.notes = notes
        self.isFavorite = isFavorite
        self.dateAdded = dateAdded
        self.year = year
    }
    
    /// Check if this is a platinum/chase variant
    var isPlatinum: Bool {
        name.localizedCaseInsensitiveContains("platinum") || 
        name.localizedCaseInsensitiveContains("chase")
    }
    
    /// Get base name without variant indicators
    var baseName: String {
        name
            .replacingOccurrences(of: " Platinum (Chase)", with: "", options: .caseInsensitive)
            .replacingOccurrences(of: " Platinum", with: "", options: .caseInsensitive)
            .replacingOccurrences(of: " (Chase)", with: "", options: .caseInsensitive)
            .trimmingCharacters(in: .whitespaces)
    }
}
