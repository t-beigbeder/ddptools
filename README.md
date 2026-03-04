# ddptools

Distributed data processing tools

- ddpbasics: basic tools useful for any data processing tools,
  local + S3 data caching among others
- ddpestorec: grpc clients to ddpestores
- ddpestores: grpc servers, see grpc directory
  - ope: general server management tool
  - stfl: state (memory dict) and flow (memory queue) remote API
  - estore: manage entities in a DB + S3-compatible objects,
    the later being indexed files containing small size data,
    useful to manage large collection of small-to-medium entities,
    such as wikipedia articles

No doc yet but test_* modules are good entry points.
