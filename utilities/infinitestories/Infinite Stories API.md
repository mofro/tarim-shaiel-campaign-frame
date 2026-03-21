## Upload options
- Single file upload (JSON, JSONL, CSV)
- Batch uploads via multipart/form-data
- Direct API upload with raw JSON in request body (application/json)
- Bulk import endpoint accepting compressed archives (zip) containing multiple files
- URL fetch import (provide a publicly accessible file URL; server fetches and ingests)
- Streaming upload for very large files (chunked/multipart with resume support)
- Web UI drag-and-drop (same-supported file types)
- Metadata-only records (no file body; metadata fields submitted via JSON)

## Schema (core fields)
Use JSON with these core fields per record (required unless noted):

- id (string) — unique identifier (UUID recommended)
- title (string) — short human-readable title
- type (string) — one of: "story", "character", "location", "item", "scene", "lore"
- language (string) — BCP-47 language tag (e.g., "en-US")
- source (string, optional) — origin or attribution
- version (string, optional) — semantic version or timestamp
- created_at (string, ISO-8601 datetime, optional)
- updated_at (string, ISO-8601 datetime, optional)
- public (boolean, default true) — visibility flag
- metadata (object, optional) — free-form key/value pairs for indexing and filtering
- tags (array[string], optional) — topic/genre tags
- content (object) — main payload, shape varies by type

## Content object shapes
- story:
  - synopsis (string)
  - body (string) — full text (Markdown allowed)
  - chapters (array of objects) — each with id, title, order (integer), body
  - recommended_level (string, optional)

- character:
  - name (string)
  - description (string)
  - age (integer, optional)
  - traits (array[string])
  - backstory (string, optional)
  - stats (object, optional) — arbitrary numeric attributes

- location:
  - name (string)
  - description (string)
  - coordinates (object, optional) — { lat: number, lng: number }
  - map_image_url (string, optional)

- item:
  - name (string)
  - description (string)
  - rarity (string, optional) — e.g., "common","rare","legendary"
  - properties (object, optional)

- scene:
  - title (string)
  - setting_id (string, optional) — link to location id
  - participants (array[string]) — character ids
  - description (string)
  - order (integer, optional)

- lore:
  - topic (string)
  - summary (string)
  - entries (array[string] or array[object])

## Validation rules
- id uniqueness enforced per import; collisions return 409 or optional upsert behavior
- Required fields per type must be present (id, type, title, content)
- Max payload size per record: typically 2–10 MB (use streaming for larger)
- Supported encodings: UTF-8
- Date fields must be ISO-8601
- Tags: max 50 tags, each max 50 chars

## Responses & error handling
- On success: 200/201 with created IDs and validation summary
- On partial success: 207 Multi-Status with per-record statuses
- On validation error: 400 with detailed field-level errors
- On conflict: 409 with existing resource id
- For large imports: async job response (202) with job_id; poll status endpoint /imports/{job_id}

## Endpoints (examples)
- POST /api/v1/uploads — single/batch upload
- POST /api/v1/imports — start bulk import (zip/url)
- POST /api/v1/uploads/stream — chunked streaming upload
- GET /api/v1/imports/{job_id} — import status
- GET /api/v1/records/{id} — fetch record
- PUT /api/v1/records/{id} — upsert record
- DELETE /api/v1/records/{id}


JSONL (JSON Lines) is a plain-text format where each line is a separate JSON object — useful for streaming and batch processing large datasets. Example differences and advice:

- JSON (application/json)
  - Structure: one JSON document (object or array).
  - Good for nested structures (arrays, objects).
  - Example (array of two records):
    ```
    [
      {"id":"1","type":"story","title":"A","content":{"body":"..." }},
      {"id":"2","type":"character","title":"B","content":{"name":"Bob"}} 
    ]
    ```

- JSONL (application/x-ndjson or text/plain)
  - Structure: one JSON object per line, no surrounding array.
  - Stream-friendly, easier to parse line-by-line, supports appending.
  - Example:
    ```
    {"id":"1","type":"story","title":"A","content":{"body":"..."}}
    {"id":"2","type":"character","title":"B","content":{"name":"Bob"}}
    ```

- CSV (text/csv)
  - Flat, tabular data only. Use for records with simple fields. Nested content should be serialized (e.g., JSON string) into a single CSV cell.
  - Example (columns: id,type,title,content):
    id,type,title,content
    1,story,"A","{\"body\":\"...\"}"
    2,character,"B","{\"name\":\"Bob\"}"

Recommendations for your upload:
- If you need nested content (chapters, traits, entries), prefer JSON or JSONL.
- Use JSONL for large/batch imports or streaming; smaller uploads can use JSON array.
- For CSV, keep a content column with serialized JSON for nested fields, and document the schema (which fields are JSON-encoded).
- Ensure UTF-8 encoding and ISO-8601 dates.
- Include header row in CSV and escape quotes/newlines in cells.

## Samples

### CSV (text/csv)
Use a header row. Nested fields are JSON-serialized in the content column.

id,type,title,language,public,source,created_at,tags,metadata,content
"f1-story-001","story","The Ember Crown","en-US","true","Grand Archives","2026-03-21","fantasy;epic;quest","{\"difficulty\":\"medium\",\"estimated_play_hours\":12}","{\"synopsis\":\"A lost crown returns to a broken kingdom.\",\"body\":\"Chapter 1: The smoldering village...\",\"chapters\":[{\"id\":\"c1\",\"title\":\"Prologue\",\"order\":1,\"body\":\"Smoke and ash...\"},{\"id\":\"c2\",\"title\":\"The Road North\",\"order\":2,\"body\":\"They rode at dawn...\"}]}"
"f1-char-001","character","Lyra Windrider","en-US","true","Campaign Creator","2026-03-20","rogue;ally","{\"alignment\":\"neutral_good\",\"origin\":\"coastal\"}","{\"name\":\"Lyra Windrider\",\"description\":\"A quick-footed thief with a heart for the downtrodden.\",\"age\":27,\"traits\":[\"agile\",\"charming\",\"resourceful\"],\"backstory\":\"Raised among docks, learned to read maps by moonlight.\",\"stats\":{\"dexterity\":18,\"strength\":10,\"charisma\":14}}"
"f1-loc-001","location","Ashen Vale","en-US","true","Cartographer Guild","2026-03-19","wilderness;haunted","{\"region\":\"north_reaches\",\"danger_level\":\"high\"}","{\"name\":\"Ashen Vale\",\"description\":\"A valley blackened by an ancient fire; cinders float like snow.\",\"coordinates\":{\"lat\":64.1234,\"lng\":-12.4321},\"map_image_url\":\"https://example.com/maps/ashen-vale.png\"}"
"f1-item-001","item","Ember Crown","en-US","false","Lost Relics","2026-03-01","artifact;legendary","{\"value\":10000,\"weight\":5}","{\"name\":\"Ember Crown\",\"description\":\"A crown of molten gold that never cools.\",\"rarity\":\"legendary\",\"properties\":{\"fire_aura\":true,\"hp_regen\":2}}"
"f1-scene-001","scene","Siege of Brindleford","en-US","true","Narrator","2026-03-15","battle;setpiece","{\"recommended_level\":\"5-7\"}","{\"title\":\"Siege of Brindleford\",\"setting_id\":\"f1-loc-001\",\"participants\":[\"f1-char-001\"],\"description\":\"Lyra sneaks through the trebuchet line as flames lick the walls.\",\"order\":3}"
"f1-lore-001","lore","Songs of the Embers","en-US","true","Bardic College","2026-02-28","myth;history","{\"era\":\"age_of_ashes\"}","{\"topic\":\"Ember Myths\",\"summary\":\"Old songs that tell of the crown's forging.\",\"entries\":[{\"title\":\"The Smith\",\"text\":\"He hammered the world into shape...\"},{\"title\":\"The Curse\",\"text\":\"Whosoever wears the crown shall burn with longing...\"}]}"


### JSON (application/json)
A single JSON array; good for nested structures.

[
  {
    "id": "f1-story-001",
    "type": "story",
    "title": "The Ember Crown",
    "language": "en-US",
    "public": true,
    "source": "Grand Archives",
    "created_at": "2026-03-21T10:00:00Z",
    "tags": ["fantasy","epic","quest"],
    "metadata": {"difficulty":"medium","estimated_play_hours":12},
    "content": {
      "synopsis": "A lost crown returns to a broken kingdom.",
      "body": "Chapter 1: The smoldering village...\n\nVillagers whispered of embers that never died.",
      "chapters": [
        {"id":"c1","title":"Prologue","order":1,"body":"Smoke and ash..."},
        {"id":"c2","title":"The Road North","order":2,"body":"They rode at dawn..."}
      ]
    }
  },
  {
    "id": "f1-char-001",
    "type": "character",
    "title": "Lyra Windrider",
    "language": "en-US",
    "public": true,
    "source": "Campaign Creator",
    "created_at": "2026-03-20T08:30:00Z",
    "tags": ["rogue","ally"],
    "metadata": {"alignment":"neutral_good","origin":"coastal"},
    "content": {
      "name": "Lyra Windrider",
      "description": "A quick-footed thief with a heart for the downtrodden.",
      "age": 27,
      "traits": ["agile","charming","resourceful"],
      "backstory": "Raised among docks, learned to read maps by moonlight.",
      "stats": {"dexterity":18,"strength":10,"charisma":14}
    }
  },
  {
    "id": "f1-loc-001",
    "type": "location",
    "title": "Ashen Vale",
    "language": "en-US",
    "public": true,
    "source": "Cartographer Guild",
    "created_at": "2026-03-19T12:00:00Z",
    "tags": ["wilderness","haunted"],
    "metadata": {"region":"north_reaches","danger_level":"high"},
    "content": {
      "name": "Ashen Vale",
      "description": "A valley blackened by an ancient fire; cinders float like snow.",
      "coordinates": {"lat":64.1234,"lng":-12.4321},
      "map_image_url": "https://example.com/maps/ashen-vale.png"
    }
  },
  {
    "id": "f1-item-001",
    "type": "item",
    "title": "Ember Crown",
    "language": "en-US",
    "public": false,
    "source": "Lost Relics",
    "created_at": "2026-03-01T09:00:00Z",
    "tags": ["artifact","legendary"],
    "metadata": {"value":10000,"weight":5},
    "content": {
      "name": "Ember Crown",
      "description": "A crown of molten gold that never cools.",
      "rarity": "legendary",
      "properties": {"fire_aura": true, "hp_regen": 2}
    }
  },
  {
    "id": "f1-scene-001",
    "type": "scene",
    "title": "Siege of Brindleford",
    "language": "en-US",
    "public": true,
    "source": "Narrator",
    "created_at": "2026-03-15T19:45:00Z",
    "tags": ["battle","setpiece"],
    "metadata": {"recommended_level":"5-7"},
    "content": {
      "title": "Siege of Brindleford",
      "setting_id": "f1-loc-001",
      "participants": ["f1-char-001"],
      "description": "Lyra sneaks through the trebuchet line as flames lick the walls.",
      "order": 3
    }
  },
  {
    "id": "f1-lore-001",
    "type": "lore",
    "title": "Songs of the Embers",
    "language": "en-US",
    "public": true,
    "source": "Bardic College",
    "created_at": "2026-02-28T07:20:00Z",
    "tags": ["myth","history"],
    "metadata": {"era":"age_of_ashes"},
    "content": {
      "topic": "Ember Myths",
      "summary": "Old songs that tell of the crown's forging.",
      "entries": [
        {"title":"The Smith","text":"He hammered the world into shape..."},
        {"title":"The Curse","text":"Whosoever wears the crown shall burn with longing..."}
      ]
    }
  }
]


### JSONL (application/x-ndjson or text/plain)
One JSON object per line (no surrounding array). Same objects as JSON above, each on its own line.

{"id":"f1-story-001","type":"story","title":"The Ember Crown","language":"en-US","public":true,"source":"Grand Archives","created_at":"2026-03-21T10:00:00Z","tags":["fantasy","epic","quest"],"metadata":{"difficulty":"medium","estimated_play_hours":12},"content":{"synopsis":"A lost crown returns to a broken kingdom.","body":"Chapter 1: The smoldering village...\n\nVillagers whispered of embers that never died.","chapters":[{"id":"c1","title":"Prologue","order":1,"body":"Smoke and ash..."},{"id":"c2","title":"The Road North","order":2,"body":"They rode at dawn..."}]}}
{"id":"f1-char-001","type":"character","title":"Lyra Windrider","language":"en-US","public":true,"source":"Campaign Creator","created_at":"2026-03-20T08:30:00Z","tags":["rogue","ally"],"metadata":{"alignment":"neutral_good","origin":"coastal"},"content":{"name":"Lyra Windrider","description":"A quick-footed thief with a heart for the downtrodden.","age":27,"traits":["agile","charming","resourceful"],"backstory":"Raised among docks, learned to read maps by moonlight.","stats":{"dexterity":18,"strength":10,"charisma":14}}}
{"id":"f1-loc-001","type":"location","title":"Ashen Vale","language":"en-US","public":true,"source":"Cartographer Guild","created_at":"2026-03-19T12:00:00Z","tags":["wilderness","haunted"],"metadata":{"region":"north_reaches","danger_level":"high"},"content":{"name":"Ashen Vale","description":"A valley blackened by an ancient fire; cinders float like snow.","coordinates":{"lat":64.1234,"lng":-12.4321},"map_image_url":"https://example.com/maps/ashen-vale.png"}}
{"id":"f1-item-001","type":"item","title":"Ember Crown","language":"en-US","public":false,"source":"Lost Relics","created_at":"2026-03-01T09:00:00Z","tags":["artifact","legendary"],"metadata":{"value":10000,"weight":5},"content":{"name":"Ember Crown","description":"A crown of molten gold that never cools.","rarity":"legendary","properties":{"fire_aura":true,"hp_regen":2}}}
{"id":"f1-scene-001","type":"scene","title":"Siege of Brindleford","language":"en-US","public":true,"source":"Narrator","created_at":"2026-03-15T19:45:00Z","tags":["battle","setpiece"],"metadata":{"recommended_level":"5-7"},"content":{"title":"Siege of Brindleford","setting_id":"f1-loc-001","participants":["f1-char-001"],"description":"Lyra sneaks through the trebuchet line as flames lick the walls.","order":3}}
{"id":"f1-lore-001","type":"lore","title":"Songs of the Embers","language":"en-US","public":true,"source":"Bardic College","created_at":"2026-02-28T07:20:00Z","tags":["myth","history"],"metadata":{"era":"age_of_ashes"},"content":{"topic":"Ember Myths","summary":"Old songs that tell of the crown's forging.","entries":[{"title":"The Smith","text":"He hammered the world into shape..."},{"title":"The Curse","text":"Whosoever wears the crown shall burn with longing..."}]}}
