// Face boxes with macOS Vision. usage: face img1.jpg img2.jpg ...
// prints one JSON line per image: [cx, cy, w, h] normalised, top-left origin, or null
import Foundation
import Vision
import AppKit
for path in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { print("null"); continue }
    let req = VNDetectFaceRectanglesRequest()
    try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
    if let r = (req.results ?? []).max(by: { $0.boundingBox.width < $1.boundingBox.width }) {
        let b = r.boundingBox
        print("[\(b.midX),\(1 - b.midY),\(b.width),\(b.height)]")
    } else { print("null") }
}
