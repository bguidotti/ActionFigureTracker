import Foundation

struct MockData {
    
    // MARK: - DC Multiverse (Real Data from Legendsverse)
    static let dcMultiverseFigures: [ActionFigure] = [
        ActionFigure(
            name: "Batman (Rainbow Suit)",
            line: .dcMultiverse,
            wave: "Detective Comics #241",
            imageName: "https://media.legendsverse.com/388092/conversions/batman-rainbow-suit-red-platinum-detective-comics-241-12270-card.jpg",
            status: .want,
            notes: "The pink one!"
        ),
        ActionFigure(
            name: "Batman (Green Suit)",
            line: .dcMultiverse,
            wave: "Detective Comics #241",
            imageName: "https://media.legendsverse.com/386721/conversions/dc-multiverse-batman-green-suit-red-platinum-6-card.jpg",
            status: .want
        ),
        ActionFigure(
            name: "Blackhawk",
            line: .dcMultiverse,
            wave: "Collector Edition #49",
            imageName: "https://media.legendsverse.com/385944/conversions/17381_07_Logos-description-card.jpg",
            status: .want
        ),
        ActionFigure(
            name: "Elongated Man",
            line: .dcMultiverse,
            wave: "Collector Edition #50",
            imageName: "https://media.legendsverse.com/385942/conversions/17382_07_Logos-description-card.jpg",
            status: .want
        ),
        ActionFigure(
            name: "Cosmic Boy",
            line: .dcMultiverse,
            wave: "Final Crisis",
            imageName: "https://media.legendsverse.com/385940/conversions/17396_07_Logos-description-card.jpg",
            status: .want
        ),
        ActionFigure(
            name: "Professor Pyg",
            line: .dcMultiverse,
            wave: "Batman Arkham",
            imageName: "https://media.legendsverse.com/385938/conversions/17397_07_Logos-description-card.jpg",
            status: .want
        ),
        ActionFigure(
            name: "Zatanna with Detective Chimp",
            line: .dcMultiverse,
            wave: "Collector Edition #53",
            imageName: "https://media.legendsverse.com/385936/conversions/17476_08_Logos-description-card.jpg",
            status: .want
        ),
        ActionFigure(
            name: "Mister Miracle (Gold Label)",
            line: .dcMultiverse,
            wave: "New Gods",
            imageName: "https://media.legendsverse.com/385946/conversions/03cadea7-6d54-41b4-b27b-4a96dd90a299-description-card.jpg",
            status: .want
        ),
        ActionFigure(
            name: "Superman (False God)",
            line: .dcMultiverse,
            wave: "Batman v Superman",
            imageName: "https://media.legendsverse.com/385948/conversions/15688CHASE_07_Logos-description-card.jpg",
            status: .want
        ),
        ActionFigure(
            name: "Green Arrow (Longbow Hunter)",
            line: .dcMultiverse,
            wave: "Gold Label",
            imageName: "https://media.legendsverse.com/385950/conversions/17172_09_LOGOS-description-card.jpg",
            status: .want
        )
    ]
    
    // MARK: - All Figures Combined
    static let allFigures: [ActionFigure] = {
        var all: [ActionFigure] = []
        all.append(contentsOf: dcMultiverseFigures)
        return all
    }()
}
