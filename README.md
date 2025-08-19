How to run version 1

# Install dependencies
pip install -r requirements.txt

# Run the analyzer
python main.py configs/ --output my_topology.json --verbose

# Expected output:
 🔹 Network Topology Analyzer - MVP Phase
# ==================================================
 1️⃣ Parsing configuration files...
   ✅ Parsed 2 devices: R1, R2
 
 2️⃣ Building network topology...
    ✅ Created topology with 1 links
 
 3️⃣ Validating network configuration...
    ✅ No configuration issues found
 
 4️⃣ Exporting topology to my_topology.json...
    ✅ Export complete
