# Learning Reference Guide
# Multi-Commodity Price Analytics Pipeline

A permanent reference for everything learned in this project.
Organized by topic, not by day. Read any chapter independently.

---

## Table of Contents

1. [Chapter 1: Project Overview](#chapter-1-project-overview)
2. [Chapter 2: Python Basics](#chapter-2-python-basics)
3. [Chapter 3: Docker & Containers](#chapter-3-docker--containers)
4. [Chapter 4: Apache Kafka](#chapter-4-apache-kafka)
5. [Chapter 5: Python & Kafka Integration](#chapter-5-python--kafka-integration)
6. [Chapter 6: Data Ingestion Patterns](#chapter-6-data-ingestion-patterns)
7. [Chapter 7: Flink Stream Processing](#chapter-7-flink-stream-processing)
8. [Chapter 8: Troubleshooting Guide](#chapter-8-troubleshooting-guide)
9. [Chapter 9: Interview Q&A](#chapter-9-interview-qa)

---

# Chapter 1: Project Overview

## What This Project Does (In Plain English)

We download Gold, Silver, Oil, and US Dollar prices from the internet and store them in Kafka (a messaging system). Later, Flink will analyze them, PostgreSQL will store results, and Power BI will visualize everything.

## Architecture

```
                         KAFKA (Filing Cabinet)
Yahoo Finance           ┌─────────────────────┐
┌──────────┐            │ gold_prices    11k   │        ┌──────────┐
│ Gold     │──Producer─→│ silver_prices  11k   │─Flink─→│PostgreSQL│──→ Power BI
│ Silver   │──Producer─→│ oil_prices     11k   │        └──────────┘
│ Oil      │──Producer─→│ usd_prices     12k   │
│ USD      │──Producer─→│                      │
└──────────┘            └─────────────────────┘
```

## Why These 4 Commodities?

| Ticker | Asset | Relationship to Gold | Why It Matters |
|--------|-------|---------------------|----------------|
| GC=F | Gold Futures | Primary asset | Our baseline |
| SI=F | Silver Futures | Moves WITH gold (~85%) | Detects positive correlation |
| CL=F | Crude Oil | Moderate (~40%) | Both are inflation hedges |
| DX-Y.NYB | US Dollar Index | Moves AGAINST gold (~-70%) | Detects inverse correlation |

When historically correlated pairs suddenly diverge, it signals anomalies — which our ML model will detect.

## File Inventory

| File | Purpose | How to Run |
|------|---------|------------|
| `docker-compose.yml` | Starts all infrastructure | `docker compose up -d` |
| `config.py` | Shared settings (broker, tickers, topics) | Imported by all scripts |
| `commodity_producer.py` | Streams live prices | `python commodity_producer.py --ticker GC=F` |
| `commodity_backfill.py` | Loads 2yr history | `python commodity_backfill.py --all` |
| `commodity_consumer.py` | Reads & displays data | `python commodity_consumer.py --all` |
| `test_tickers.py` | Verifies tickers work | `python test_tickers.py` |

---

# Chapter 2: Python Basics

Quick reference for every Python concept used in our scripts.

## How Developers Actually Code

Nobody writes 183 lines in one go. The real process:
1. Say what you want in English: "I need to download gold prices"
2. Break it into small steps: "fetch data → loop through → send each one"
3. Google the syntax for each step
4. Write 3 lines. Run it. See if it works.
5. Fix errors. Add 3 more lines. Repeat.

## Variables (Labels for Values)

```python
name = "Gold"       # Text (string)
price = 5094.20     # Decimal number (float)
count = 100         # Whole number (int)
```

`=` means "store", NOT "equals." After `name = "Gold"`, typing `name` gives you `"Gold"`.

## Lists (Ordered Collections)

```python
fruits = ["apple", "banana", "mango"]
fruits[0]              # "apple" (counting starts at 0)
fruits.append("grape") # adds to end
len(fruits)            # 4 (how many items)
```

## Dictionaries (Key → Value Lookup)

```python
person = {"name": "Ali", "age": 25}
person["name"]         # "Ali"
person["age"]          # 25
```

Nested (dict inside dict):
```python
COMMODITIES["GC=F"]["name"]    # "Gold"
```

## Functions (Saved Recipes)

```python
def greet(name):         # Save a recipe. name = input it needs.
    return "Hello " + name

greet("Ali")             # "Hello Ali" — runs the recipe
```

- `def` = define (save). Does NOT run yet.
- `return` = give back a result.
- `()` at the end = run it NOW.

## For Loops (Repeat for Each Item)

```python
for fruit in ["apple", "banana"]:
    print(fruit)
# prints: apple, then banana
```

## If / Else (Make a Decision)

```python
if age > 18:
    print("adult")
else:
    print("minor")
```

## F-Strings (Insert Variables into Text)

```python
name = "Gold"
print(f"Price of {name} is high")    # Price of Gold is high
```

The `f` before quotes lets you put `{variables}` inside text.

## Useful Extras

| Syntax | What it Does | Example |
|--------|-------------|---------|
| `+=` | Add and update | `count += 1` (count goes up by 1) |
| `%` | Remainder | `10 % 3` gives `1` |
| `"=" * 60` | Repeat text | A long line of `=====` |
| `.lower()` | Lowercase | `"GOLD".lower()` → `"gold"` |
| `.keys()` | Get dict keys | `{"a": 1}.keys()` → `["a"]` |
| `json.dumps(d)` | Dict → JSON text | For sending to Kafka |
| `time.sleep(5)` | Pause 5 seconds | Rate limiting |
| `continue` | Skip to next loop round | Skip bad data |

## The `if __name__` Guard

```python
if __name__ == "__main__":
    main()
```

"Only run `main()` if this file was executed directly, not imported."

---

# Chapter 2: Docker & Containers

## What Is Docker?

**Analogy:** A shipping container for software. Package once, run anywhere.

| Term | Definition |
|------|------------|
| **Image** | A blueprint/recipe. Read-only template to create a container. |
| **Container** | A running instance of an image. Isolated but shares your PC's resources. |
| **Docker Hub** | Online store for images. |
| **Docker Compose** | Tool to run multiple containers at once using a YAML file. |

## Why Docker? (Not for Performance)

Docker does NOT make things lighter. It uses the same CPU, RAM, and disk.

| Benefit | Without Docker | With Docker |
|---------|---------------|-------------|
| **Installation** | Install Java 11, set JAVA_HOME, debug PATH | `docker compose up -d` |
| **Networking** | Manually configure IPs, firewall rules | Services find each other by name |
| **Reproducibility** | "It works on my machine" | Works identically on any machine |
| **Cleanup** | Leftover files, env vars, registry keys | `docker compose down` removes everything |

## Docker Networking

When you run `docker compose up -d`, Docker creates a private network. All services join automatically.

```
┌───────────────────────────────────────────────────┐
│      Docker Network: end_to_end_project_default    │
│                                                    │
│  zookeeper ←──→ kafka ←──→ kafdrop                │
│                   ↕                                │
│         flink-jobmanager ←──→ flink-taskmanager   │
│                                                    │
│  All find each other BY NAME (Docker DNS)          │
└───────────────────────────────────────────────────┘
        ↑
        │ port mappings (localhost:9092, localhost:8081, etc.)
        ↓
┌──────────────────┐
│  YOUR WINDOWS PC  │
│  Python scripts   │
│  Browser          │
└──────────────────┘
```

**Two worlds:**
- Container-to-container: use service name (`kafka:29092`)
- Your PC-to-container: use localhost (`localhost:9092`)

## YAML Basics

Docker Compose uses YAML, a configuration format:
- **Indentation matters** — Use 2 spaces (never tabs)
- **Key-Value pairs** — `name: value`
- **Lists** — Start with `-`

```yaml
services:
  service_name:
    image:          # What software to download
    container_name: # Nickname for easy reference
    ports:
      - "HOST:CONTAINER"
    environment:
      KEY: value
    depends_on:
      - other_service
```

## Docker Data Persistence

| Action | Data Survives? |
|--------|----------------|
| Close Antigravity / VS Code | ✅ Yes — Docker is independent |
| Shut down PC, then `docker compose start` | ✅ Yes |
| `docker compose stop` then `start` | ✅ Yes |
| `docker compose down` | ❌ No — containers destroyed |
| `docker compose down -v` | ❌ No — everything destroyed |

To make data permanent, add `volumes:` to docker-compose.yml.

## Essential Docker Commands

```bash
docker compose up -d           # Start all services (background)
docker compose down            # Stop and remove all containers
docker compose ps              # View running services
docker compose logs -f kafka   # Follow Kafka logs
docker compose restart kafka   # Restart a specific service
docker ps                      # List running containers
docker exec kafka <command>    # Run command inside a container
docker network inspect <name>  # See container IP addresses
```

---

# Chapter 3: Apache Kafka

## What Is Kafka? (Simple Version)

**Kafka is a filing cabinet with magical powers.** Programs put messages in (producers) and other programs read them out (consumers). Messages stay in the cabinet even after reading.

| Term | Definition |
|------|------------|
| **Broker** | A Kafka server. Stores and serves messages. |
| **Topic** | A named "drawer" in the filing cabinet. |
| **Partition** | A slice of a topic for parallel processing. |
| **Producer** | Program that WRITES messages to a topic. |
| **Consumer** | Program that READS messages from a topic. |
| **Offset** | Bookmark — which message you've read up to. |
| **Consumer Group** | A team of consumers sharing the workload. |

## Kafka Architecture

```
Producers                  Kafka Broker                    Consumers
┌────────┐                ┌──────────────┐                ┌────────┐
│Gold    │──writes──→     │gold_prices   │──reads──→      │Consumer│
│Producer│                │ [msg1][msg2] │                │        │
└────────┘                │ [msg3][msg4] │                └────────┘
                          │ ...          │
┌────────┐                │silver_prices │                ┌────────┐
│Silver  │──writes──→     │ [msg1][msg2] │──reads──→      │Flink   │
│Producer│                │              │                │(later) │
└────────┘                └──────────────┘                └────────┘
```

## How Offsets Work (The Bookmark)

- `auto.offset.reset = 'earliest'`: Start from message #1 **only if no bookmark exists yet**
- First run: No bookmark → reads all 11,462 messages
- Second run: Bookmark at #11,462 → starts from #11,463 (only new messages)
- Consumer crashes at #5,000 → restarts from #5,000 (no data loss)

## Event Time vs Arrival Order

**Critical concept:**
- Kafka stores messages in **ARRIVAL order** (first-come, first-served)
- Kafka does NOT sort by timestamp
- If you run live producer first, then backfill → timestamps are shuffled
- **Our fix:** Run backfill first, then live producer → data stays chronological
- **Flink's fix:** Event-time processing — sorts by timestamp inside the message, regardless of arrival order

## Docker Compose Configuration

```yaml
kafka:
  image: confluentinc/cp-kafka:7.5.0
  depends_on:
    - zookeeper
  ports:
    - "9092:9092"       # Your PC connects here
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

**The Advertised Listeners Pitfall (#1 Kafka connection error):**
- `kafka:29092` → For containers talking to Kafka (Flink, Kafdrop)
- `localhost:9092` → For your Python scripts on Windows

## Zookeeper

**Analogy:** The manager of the filing cabinet. Tracks which brokers are alive.
```yaml
zookeeper:
  image: confluentinc/cp-zookeeper:7.5.0
  environment:
    ZOOKEEPER_CLIENT_PORT: 2181
    ZOOKEEPER_TICK_TIME: 2000
```

## Kafdrop (The Visual UI)

Web interface to peek inside Kafka at [http://localhost:9000](http://localhost:9000).
Must use `kafka:29092` (internal address), NOT `localhost:9092`.

## Essential Kafka CLI Commands

```bash
# List all topics
docker exec kafka kafka-topics --list --bootstrap-server kafka:29092

# Describe a topic
docker exec kafka kafka-topics --describe --topic gold_prices --bootstrap-server kafka:29092

# Read messages from beginning
docker exec kafka kafka-console-consumer --topic gold_prices --from-beginning --bootstrap-server kafka:29092

# Check consumer lag
docker exec kafka kafka-consumer-groups --bootstrap-server kafka:29092 --group <group_id> --describe
```

---

# Chapter 4: Python & Kafka Integration

## The Two Patterns

| Aspect | Producer | Consumer |
|--------|----------|----------|
| **Job** | WRITE data to Kafka | READ data from Kafka |
| **Library** | `confluent_kafka.Producer` | `confluent_kafka.Consumer` |
| **Key method** | `producer.produce()` | `consumer.poll()` |
| **Needs group.id?** | No | Yes |

## Producer Pattern (Simplified)

```python
from confluent_kafka import Producer
import json

producer = Producer({"bootstrap.servers": "localhost:9092"})

data = {"ticker": "GC=F", "price": 5094.20}
producer.produce("gold_prices", json.dumps(data).encode("utf-8"))
producer.flush()   # Wait for delivery
```

**What happens:**
1. Connect to Kafka at `localhost:9092`
2. Convert Python dict → JSON string → bytes
3. Send bytes to the `gold_prices` topic
4. `flush()` waits until Kafka confirms receipt

## Consumer Pattern (Simplified)

```python
from confluent_kafka import Consumer
import json

consumer = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "my-reader",            # Your name tag
    "auto.offset.reset": "earliest",    # Start from first message
})

consumer.subscribe(["gold_prices"])     # Pick which topic to read

while True:
    msg = consumer.poll(timeout=1.0)    # Ask: "Any new messages?"
    if msg is None: continue            # Nothing? Ask again.
    data = json.loads(msg.value())      # bytes → JSON → Python dict
    print(data)                         # Do something with it
```

**What happens:**
1. Connect to Kafka and say "I'm in group my-reader"
2. Subscribe to `gold_prices` topic
3. Loop forever: ask for messages, process them, repeat

## Virtual Environments (venv)

Each project has isolated Python dependencies. No version conflicts.

```powershell
python -m venv venv                  # Create (once)
.\venv\Scripts\Activate.ps1          # Activate (every terminal)
pip install -r requirements.txt      # Install dependencies
deactivate                           # Exit venv
```

---

# Chapter 5: Data Ingestion Patterns

## Backfill vs Live Streaming

| Pattern | Script | Frequency | Purpose |
|---------|--------|-----------|---------|
| **Backfill** | `commodity_backfill.py` | Run ONCE | Load 2 years of history |
| **Live** | `commodity_producer.py` | Run FOREVER | Stream new prices every 5s |

**The correct order:**
1. Start Kafka (`docker compose up -d`)
2. Run backfill first (`python commodity_backfill.py --all`)
3. Then start live producers (in separate terminals)

## The DRY Principle

Instead of 4 identical producer files, one generic script handles all commodities:

```python
# config.py — Single source of truth
COMMODITIES = {
    "GC=F": {"topic": "gold_prices", "name": "Gold Futures"},
    "SI=F": {"topic": "silver_prices", "name": "Silver Futures"},
    ...
}
```

Adding a 5th commodity = one line in config.py, zero code changes elsewhere.

## argparse (CLI Arguments)

```python
parser.add_argument("--ticker", choices=["GC=F", "SI=F", ...])
```

Makes scripts self-documenting: `python commodity_producer.py --help` shows usage.

## Rate Limiting

Yahoo Finance throttles rapid API calls. Fix: add `time.sleep(3)` between requests.
Our backfill waits 5 seconds between commodities.

## API Resilience

Yahoo Finance goes down sometimes. The producer handles this:
1. Try `fast_info` first (fast)
2. Fall back to `.history()` (slower but more reliable)
3. If both fail, skip and retry next cycle

---

# Chapter 6: Flink Stream Processing

## What Is Flink?

**One sentence:** Flink is a smart consumer that remembers, recovers, and scales.

A Python consumer reads one message, prints it, forgets it. Flink reads a message and **remembers** it — so it can calculate things like "the average of the last 20 prices."

| Feature | Python Consumer | Flink |
|---------|----------------|-------|
| Read from Kafka | ✅ | ✅ |
| Process each message | ✅ | ✅ |
| Remember last 20 prices for SMA | ❌ Manual coding | ✅ Built-in windows |
| Recover from crash | ❌ Starts over | ✅ Resumes from checkpoint |
| Run on 100 machines | ❌ | ✅ Auto-distributes |

## The 3 Superpowers of Flink

### 1. State (Memory)
Your consumer sees `Gold: $5094` and immediately forgets. Flink sees `Gold: $5094` and records it: "That's the 20th price. The last 20 prices average to $5087."

### 2. Checkpoints (Recovery)
Every 10 seconds, Flink saves progress to disk: "I'm at message #5000, running average is $5087." If it crashes and restarts, it resumes from that exact point. No data loss, no re-processing.

### 3. Parallelism (Scaling)
Your Python script uses one CPU core. Flink splits work across multiple TaskManagers automatically: "TM1 handles Gold+Silver, TM2 handles Oil+USD."

## Architecture (Coordinator-Worker Pattern)

This pattern appears in ALL distributed systems:

| System | Coordinator (Boss) | Worker |
|--------|-------------------|--------|
| **Flink** | JobManager | TaskManager |
| **Kafka** | Zookeeper | Broker |
| **Kubernetes** | Master Node | Worker Node |
| **Spark** | Driver | Executor |

```
     YOU write a job (Python script)
              │
              ▼
     ┌──────────────────┐
     │   JOB MANAGER    │  Reads your job, splits into tasks,
     │   (The Boss)     │  assigns to workers, tracks progress
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────────────────┐
     │       TASK MANAGER           │  Executes the actual work
     │  ┌────────┐  ┌────────┐    │
     │  │ Slot 1 │  │ Slot 2 │    │  2 slots = 2 parallel tasks
     │  │ Gold   │  │ Silver │    │
     │  └────────┘  └────────┘    │
     └──────────────────────────────┘
```

## How You Control Work Distribution

Flink auto-distributes by default. You control the **strategy**, not individual assignments:

| Lever | What You Say | What Flink Does |
|-------|-------------|-----------------|
| **Parallelism** | "Use 4 parallel workers" | Creates 4 instances, assigns to slots |
| **key_by** | "Group by ticker" | All Gold messages → same worker, all Silver → same worker |
| **Slot sharing** | "These tasks can share a slot" | Packs tasks efficiently |

**key_by is the most important** — if Gold prices are scattered across workers, no single worker can compute a correct moving average:

```
Without key_by (BAD):
  Slot 1: Gold $5090, Silver $82, Gold $5094   ← Gold scattered, SMA wrong

With key_by("ticker") (GOOD):
  Slot 1: Gold $5090, Gold $5092, Gold $5094   ← All gold → correct SMA
  Slot 2: Silver $82, Silver $83, Oil $66
```

## Dashboard & Resource Usage

Access at [http://localhost:8081](http://localhost:8081)

| What to Check | Where | Our Value |
|---------------|-------|-----------|
| Task Managers connected | Task Managers tab | 1 |
| Available task slots | Overview | 2 |
| Running jobs | Overview | 0 (until we submit one) |
| Memory limit | Task Managers tab | 7.63 GB |
| Actual memory used | `docker stats --no-stream` | ~300-700 MB |

**Key insight:** The 7.63 GB is a LIMIT (credit card limit), not what's actually used (current balance). With no jobs, the TaskManager idles at ~300-700 MB. Docker containers don't pre-reserve memory like VMs.

## Flink Config File Deep Dive

**How to view:** `docker exec flink-jobmanager cat /opt/flink/conf/flink-conf.yaml`

The config file has 100+ lines but only 3 are active (uncommented). Everything else is a template for production features.

### Active Settings (These Matter)

| Config | Value | Purpose |
|--------|-------|---------|
| `jobmanager.rpc.address` | `flink-jobmanager` | How TaskManagers find the boss. If wrong → workers sit idle. |
| `blob.server.port` | `6124` | Port for uploading job files (JARs) to JobManager |
| `query.server.port` | `6125` | Port for querying Flink's internal state from outside |

### Commented-Out Settings (Production Only — Ignore for Now)

| Section | What | When You Need It |
|---------|------|-----------------|
| Checkpointing | Auto-save progress to disk | Production jobs processing millions of messages |
| High Availability | Multiple JobManagers for failover | When downtime costs money |
| Zookeeper Security | Kerberos authentication | Corporate environments with security policies |
| io.tmp.dirs | Temp file location | When you have fast SSDs for temp data |
| Network buffers | RAM for shuffling between workers | Processing >1M messages/sec |
| HistoryServer | View completed jobs history | Reviewing past job performance |

**Analogy — Car dashboard:** You use the speedometer and fuel gauge daily. The OBD-II diagnostic port exists but you only need it when something breaks.

## Kafka Connector Setup

Flink doesn't know how to talk to Kafka by default. It needs a **connector JAR** — like Python needs `pip install confluent-kafka`.

```bash
# Download Kafka connector into the Flink container
docker exec flink-jobmanager bash -c \
  "cd /opt/flink/lib && curl -O https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.0.2-1.18/flink-sql-connector-kafka-3.0.2-1.18.jar"
```

**Why inside the container?** Java (needed by Flink) is inside Docker, not on your PC. This is exactly why we use Docker — no need to install Java on Windows.

## Docker Compose Configuration

```yaml
flink-jobmanager:
  image: flink:1.18.0-scala_2.12
  ports:
    - "8081:8081"        # Dashboard
  command: jobmanager
  environment:
    FLINK_PROPERTIES: |
      jobmanager.rpc.address: flink-jobmanager

flink-taskmanager:
  image: flink:1.18.0-scala_2.12
  depends_on:
    - flink-jobmanager
  command: taskmanager
  environment:
    FLINK_PROPERTIES: |
      jobmanager.rpc.address: flink-jobmanager
      taskmanager.numberOfTaskSlots: 2
```

`FLINK_PROPERTIES` gets written into `flink-conf.yaml` inside the container on startup.

## Useful Flink Commands

```bash
# Check Flink config
docker exec flink-jobmanager cat /opt/flink/conf/flink-conf.yaml

# View JobManager logs
docker logs flink-jobmanager --tail 20

# View TaskManager logs
docker logs flink-taskmanager --tail 20

# Check actual resource usage (all containers)
docker stats --no-stream
```

---

# Chapter 7: Troubleshooting Guide

## Docker Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `open //./pipe/dockerDesktopLinuxEngine` | Docker Desktop not running | Open Docker Desktop, wait for green status |
| Containers start but scripts fail | Kafka not fully initialized (cold start) | Wait 10-15 seconds after `docker compose up` |
| `Connection Refused` | Service not ready or wrong address | Check `docker compose ps`, verify ports |

## Kafka Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `NoBrokersAvailable` | Kafka not running | `docker compose up -d` |
| `Leader Not Available` | Kafka still initializing | Wait 10 seconds |
| Consumer gets no messages | Wrong group.id or already read all | Use new group.id or `auto.offset.reset: earliest` |
| Zombie consumer (hangs) | Force-quit terminal, old consumer still registered | `docker compose restart kafka` |
| Scripts use `kafka:9092` | Wrong address from Windows | Use `localhost:9092` from Windows |
| Kafdrop uses `localhost:9092` | Wrong address from inside Docker | Use `kafka:29092` from containers |

## Python Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError` | venv not activated | `.\venv\Scripts\Activate.ps1` |
| `UnknownTopicOrPartition` | Topic doesn't exist | Run producer/backfill first to auto-create |
| Yahoo Finance returns $0 or empty | API down or rate limited | Wait and retry, add `time.sleep()` between calls |
| All tickers fail at once | Yahoo Finance rate limiting | Test one at a time with 3s delays |

## Flink Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Dashboard shows 0 TaskManagers | TaskManager can't find JobManager | Check `jobmanager.rpc.address` in FLINK_PROPERTIES |
| "ClassNotFoundException: KafkaSource" | Kafka connector JAR not installed | Download connector JAR into `/opt/flink/lib/` |
| Job fails with "No slots available" | All task slots are in use | Increase `taskmanager.numberOfTaskSlots` or add more TaskManagers |
| Job runs but no output | Wrong Kafka address from inside container | Use `kafka:29092`, not `localhost:9092` |

---

# Chapter 8: Interview Q&A

**Q: Describe your project in 30 seconds.**
> I built a real-time pipeline that ingests Gold, Silver, Oil, and US Dollar prices from Yahoo Finance into Kafka, processes them with Flink to compute moving averages and cross-commodity correlations, stores results in PostgreSQL, and uses Isolation Forest to detect anomalies — like when gold spikes without the dollar dropping, which signals unusual market activity.

**Q: What does a Kafka consumer do?**
> It connects to a Kafka broker, subscribes to a specific topic, reads messages one by one, and processes them. In my project, the consumer reads commodity price data and displays it.

**Q: What does a Kafka producer do?**
> It fetches data from an external source (Yahoo Finance API) and writes it as JSON messages to a Kafka topic.

**Q: Why did you use Docker?**
> Production parity. In production, these services run in Kubernetes containers. Docker Compose makes the project reproducible — anyone can clone and run `docker compose up -d`. It also handles networking — services discover each other by name through Docker's internal DNS.

**Q: Why Kafka and not just a CSV file?**
> I had 4 independent data streams consumed by multiple downstream systems. Kafka provides durable ordered storage, offset tracking for exactly-once processing, and decouples producers from consumers.

**Q: What happens when your data source goes down?**
> The producer logs the failure and retries on the next cycle. Kafka retains all existing data. When the source recovers, the pipeline resumes. No data loss — only a gap in the source data.

**Q: What if data arrives out of order?**
> Kafka stores in arrival order, not by timestamp. Flink handles this with event-time processing — it uses the timestamp inside each message to process chronologically, regardless of arrival order.

**Q: Why one generic producer instead of 4 files?**
> DRY principle. One parameterized script handles all commodities via argparse. Adding a new asset is one config line, zero code changes.

**Q: What is Flink and why use it?**
> Flink is a distributed stream processing engine. Unlike a Python consumer that reads-and-forgets, Flink maintains state (remembers previous prices for calculations), checkpoints its progress for crash recovery, and auto-distributes work across machines. I used it to compute rolling moving averages and cross-commodity correlations in real-time.

**Q: What's the difference between JobManager and TaskManager?**
> JobManager is the coordinator — reads the job definition, splits it into tasks, assigns work to workers. TaskManager is the worker — executes the actual data processing in "task slots." This coordinator-worker pattern is universal: Spark has Driver/Executor, Kafka has Zookeeper/Broker.

**Q: How does Flink distribute work?**
> You set the parallelism (how many workers) and key_by (how to group data). key_by ensures all messages with the same key go to the same worker — critical for stateful operations like moving averages. Flink handles the rest (scheduling, slot assignment).

**Q: Does Docker reserve all that memory?**
> No. Docker containers share host resources with configurable limits. A TaskManager configured for 8 GB might only use 300 MB at idle. The limit prevents runaway memory usage. It's a ceiling, not a reservation — unlike VMs which pre-allocate.

**Q: Why did you choose these specific commodities?**
> They have known economic relationships. Gold and silver are positively correlated (~85%), gold and USD are inversely correlated (~-70%). When these relationships break, it signals anomalies worth investigating.
