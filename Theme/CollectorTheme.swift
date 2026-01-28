//
//  CollectorTheme.swift
//  ActionFigureTracker
//
//  High-end collector's dashboard theme
//

import SwiftUI

// MARK: - Theme Colors

enum CollectorTheme {
    // Core Colors
    static let background = Color(hex: "121212")
    static let cardBackground = Color(hex: "1E1E1E")
    static let surfaceBackground = Color(hex: "2A2A2A")
    static let textPrimary = Color(hex: "F5F5F5")
    static let textSecondary = Color(hex: "A0A0A0")
    
    // Accent Colors
    static let accentGold = Color(hex: "D4AF37")
    static let accentPlatinum = Color(hex: "E5E4E2")
    
    // Status Colors
    static let statusHave = Color(hex: "00C853") // Bright green
    static let statusWant = Color(hex: "FF9100") // Amber
    static let statusHaveGlow = Color(hex: "00E676")
    
    // Card Styling
    static let cardCornerRadius: CGFloat = 20
    static let cardStrokeColor = Color.white.opacity(0.1)
    static let cardStrokeWidth: CGFloat = 1
    static let cardShadowColor = Color.black.opacity(0.3)
    static let cardShadowRadius: CGFloat = 10
    static let cardShadowY: CGFloat = 5
    
    // Typography
    static let trackingWide: CGFloat = 1.5
}

// MARK: - Color Extension for Hex

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

// MARK: - View Modifiers

struct BentoCardModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .background(CollectorTheme.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: CollectorTheme.cardCornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: CollectorTheme.cardCornerRadius)
                    .stroke(CollectorTheme.cardStrokeColor, lineWidth: CollectorTheme.cardStrokeWidth)
            )
            .shadow(
                color: CollectorTheme.cardShadowColor,
                radius: CollectorTheme.cardShadowRadius,
                x: 0,
                y: CollectorTheme.cardShadowY
            )
    }
}

struct GlassmorphismModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .background(.ultraThinMaterial)
    }
}

extension View {
    func bentoCard() -> some View {
        modifier(BentoCardModifier())
    }
    
    func glassmorphism() -> some View {
        modifier(GlassmorphismModifier())
    }
}

// MARK: - Pro Typography Styles

struct ProTypography {
    static func figureName() -> some View {
        EmptyView()
    }
}

extension View {
    func figureNameStyle() -> some View {
        self.font(.system(.headline, design: .monospaced))
            .foregroundStyle(CollectorTheme.textPrimary)
    }
    
    func seriesLabelStyle() -> some View {
        self.font(.system(.subheadline, design: .default, weight: .semibold))
            .textCase(.uppercase)
            .tracking(CollectorTheme.trackingWide)
            .foregroundStyle(CollectorTheme.textSecondary)
    }
}
