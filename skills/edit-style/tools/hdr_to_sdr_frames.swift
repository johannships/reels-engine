// Decode an HDR (HLG/Dolby Vision) iPhone clip with Apple's own HDR->SDR tone map (AVAssetReader, BT.709 output)
// and write the frames listed in need.txt (indices at 60 fps) as JPEGs at W x H.
import AVFoundation; import CoreImage; import ImageIO; import UniformTypeIdentifiers
let a = CommandLine.arguments
let src = URL(fileURLWithPath: a[1]); let needPath = a[2]; let outDir = a[3]
let W = Double(a[4])!, H = Double(a[5])!, FPS = Double(a[6])!
let need = Set(try! String(contentsOfFile: needPath, encoding: .utf8).split(separator: " ").compactMap { Int($0.trimmingCharacters(in: .whitespacesAndNewlines)) })
let asset = AVURLAsset(url: src)
let track = asset.tracks(withMediaType: .video)[0]
let reader = try! AVAssetReader(asset: asset)
let settings: [String: Any] = [
  kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
  AVVideoColorPropertiesKey: [AVVideoColorPrimariesKey: AVVideoColorPrimaries_ITU_R_709_2,
                              AVVideoTransferFunctionKey: AVVideoTransferFunction_ITU_R_709_2,
                              AVVideoYCbCrMatrixKey: AVVideoYCbCrMatrix_ITU_R_709_2]]
let out = AVAssetReaderTrackOutput(track: track, outputSettings: settings)
out.alwaysCopiesSampleData = false
reader.add(out); reader.startReading()
let cs = CGColorSpace(name: CGColorSpace.itur_709)!
let ctx = CIContext(options: [.workingColorSpace: cs, .outputColorSpace: cs])
var written = 0
// VFR source (30/60 mixed): mirror ffmpeg fps=60 -- each decoded frame covers indices round(t*FPS) ..< round(t_next*FPS)
func save(_ pb: CVPixelBuffer, _ i: Int) {
  let p = "\(outDir)/s\(String(format: "%05d", i)).jpg"
  var img = CIImage(cvPixelBuffer: pb, options: [.colorSpace: cs])
  let sx = W / img.extent.width, sy = H / img.extent.height
  let f = CIFilter(name: "CILanczosScaleTransform")!
  f.setValue(img, forKey: kCIInputImageKey); f.setValue(sy, forKey: kCIInputScaleKey); f.setValue(sx / sy, forKey: kCIInputAspectRatioKey)
  img = f.outputImage!.cropped(to: CGRect(x: 0, y: 0, width: W, height: H))
  let cg = ctx.createCGImage(img, from: CGRect(x: 0, y: 0, width: W, height: H), format: .RGBA8, colorSpace: cs)!
  let d = CGImageDestinationCreateWithURL(URL(fileURLWithPath: p) as CFURL, UTType.jpeg.identifier as CFString, 1, nil)!
  CGImageDestinationAddImage(d, cg, [kCGImageDestinationLossyCompressionQuality: 0.94] as CFDictionary)
  CGImageDestinationFinalize(d); written += 1
}
var prev: CMSampleBuffer? = nil; var prevI = 0
func flush(_ upTo: Int) {
  guard let ps = prev, let pb = CMSampleBufferGetImageBuffer(ps) else { return }
  var i = prevI
  while i < upTo { if need.contains(i) { save(pb, i) }; i += 1 }
}
while let sb = out.copyNextSampleBuffer() {
  guard CMSampleBufferGetImageBuffer(sb) != nil else { continue }
  let i = Int((CMSampleBufferGetPresentationTimeStamp(sb).seconds * FPS).rounded())
  flush(max(i, prevI)); prev = sb; prevI = max(i, prevI)
}
flush(prevI + 2)
print("DONE written=\(written) need=\(need.count) status=\(reader.status.rawValue)")
