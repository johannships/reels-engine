// Text in images with macOS Vision. usage: ocr img1.jpg img2.jpg ...
// prints: <basename>\t<line> | <line> ...
import Foundation
import Vision
import AppKit
for path in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { print("\(path)\tERR"); continue }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = false
    try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
    let lines = (req.results ?? []).compactMap { $0.topCandidates(1).first?.string }
    print("\((path as NSString).lastPathComponent)\t\(lines.joined(separator: " | "))")
}
