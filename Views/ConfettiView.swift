//
//  ConfettiView.swift
//  ActionFigureTracker
//
//  Fun confetti animation when you get a new figure!
//

import SwiftUI

struct ConfettiView: View {
    let isShowing: Bool
    
    @State private var particles: [ConfettiParticle] = []
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                ForEach(particles) { particle in
                    Circle()
                        .fill(particle.color)
                        .frame(width: particle.size, height: particle.size)
                        .position(particle.position)
                        .opacity(particle.opacity)
                }
            }
        }
        .allowsHitTesting(false)
        .onChange(of: isShowing) { _, newValue in
            if newValue {
                createConfetti()
            } else {
                particles = []
            }
        }
    }
    
    private func createConfetti() {
        particles = (0..<50).map { _ in
            ConfettiParticle(
                color: [.red, .blue, .green, .yellow, .purple, .orange, .pink].randomElement()!,
                size: CGFloat.random(in: 8...16),
                position: CGPoint(
                    x: CGFloat.random(in: 0...UIScreen.main.bounds.width),
                    y: CGFloat.random(in: 0...UIScreen.main.bounds.height)
                ),
                opacity: 1
            )
        }
        
        // Animate particles falling
        withAnimation(.easeOut(duration: 2)) {
            particles = particles.map { particle in
                var newParticle = particle
                newParticle.position.y += CGFloat.random(in: 100...300)
                newParticle.position.x += CGFloat.random(in: -50...50)
                newParticle.opacity = 0
                return newParticle
            }
        }
    }
}

struct ConfettiParticle: Identifiable {
    let id = UUID()
    var color: Color
    var size: CGFloat
    var position: CGPoint
    var opacity: Double
}

#Preview {
    ZStack {
        Color.white
        ConfettiView(isShowing: true)
    }
}
