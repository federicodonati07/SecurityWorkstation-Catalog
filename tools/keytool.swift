// Ed25519 key management and signing for the catalog (CryptoKit, no dependencies).
//   swift tools/keytool.swift keygen <private-key-file> <public-key-b64-file> <public-key-pem-file>
//   swift tools/keytool.swift sign   <private-key-file> <file>            -> prints base64 signature
//   swift tools/keytool.swift verify <public-key-b64-file> <file> <sig-file>
// The private key is a base64 32-byte seed. KEEP IT OUTSIDE THE REPOSITORY (default: ~/.config/security-workstation/).
import Foundation
import CryptoKit

func fail(_ message: String) -> Never { FileHandle.standardError.write(Data((message + "\n").utf8)); exit(1) }
let args = CommandLine.arguments
guard args.count >= 3 else { fail("usage: keytool.swift keygen|sign|verify …") }

switch args[1] {
case "keygen":
    guard args.count == 5 else { fail("keygen <private-file> <public-b64-file> <public-pem-file>") }
    if FileManager.default.fileExists(atPath: args[2]) { fail("refusing to overwrite existing private key \(args[2])") }
    let key = Curve25519.Signing.PrivateKey()
    let dir = URL(fileURLWithPath: args[2]).deletingLastPathComponent()
    try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
    try (key.rawRepresentation.base64EncodedString() + "\n").write(toFile: args[2], atomically: true, encoding: .utf8)
    try FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: args[2])
    let pub = key.publicKey.rawRepresentation
    try (pub.base64EncodedString() + "\n").write(toFile: args[3], atomically: true, encoding: .utf8)
    // SPKI wrapper for OpenSSL: 302a300506032b6570032100 || raw key
    let spki = Data([0x30, 0x2a, 0x30, 0x05, 0x06, 0x03, 0x2b, 0x65, 0x70, 0x03, 0x21, 0x00]) + pub
    let b64 = spki.base64EncodedString()
    try "-----BEGIN PUBLIC KEY-----\n\(b64)\n-----END PUBLIC KEY-----\n".write(toFile: args[4], atomically: true, encoding: .utf8)
    print("public key: \(pub.base64EncodedString())")
case "sign":
    guard args.count == 4, let seed = (try? String(contentsOfFile: args[2], encoding: .utf8))?.trimmingCharacters(in: .whitespacesAndNewlines),
          let raw = Data(base64Encoded: seed), let key = try? Curve25519.Signing.PrivateKey(rawRepresentation: raw),
          let data = FileManager.default.contents(atPath: args[3]) else { fail("sign <private-key-file> <file>: cannot read key or file") }
    print(try key.signature(for: data).base64EncodedString())
case "verify":
    guard args.count == 5, let pubText = (try? String(contentsOfFile: args[2], encoding: .utf8))?.trimmingCharacters(in: .whitespacesAndNewlines),
          let raw = Data(base64Encoded: pubText), let pub = try? Curve25519.Signing.PublicKey(rawRepresentation: raw),
          let data = FileManager.default.contents(atPath: args[3]),
          let sigText = (try? String(contentsOfFile: args[4], encoding: .utf8))?.trimmingCharacters(in: .whitespacesAndNewlines),
          let sig = Data(base64Encoded: sigText) else { fail("verify <public-b64-file> <file> <sig-file>: cannot read inputs") }
    if pub.isValidSignature(sig, for: data) { print("signature OK") } else { fail("SIGNATURE INVALID") }
default: fail("unknown command \(args[1])")
}
