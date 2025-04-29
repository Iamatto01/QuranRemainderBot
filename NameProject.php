<!DOCTYPE html>
<html lang="en">
<meta name="viewport" content="width=device-width, initial-scale=1">
<head>
    <meta charset="utf-8">
    <title>Name Record</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
        }
        #nameList {
            margin-top: 10px;
            width: 200px;
            height: 200px;
            overflow-y: auto;
            border: 1px solid #000;
            padding: 5px;
            background-color: #fff;
        }
        .selected {
            background-color: #ADD8E6; /* Light blue */
        }
        button {
            background-color: #4CAF50; /* Green */
            border: none;
            color: white;
            padding: 15px 32px;
            text-align: center;
            text-debamboicoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <?php
    // Database configuration
    $dbhost = "localhost";
    $dbuser = "SYSTEM";
    $dbpassword = "Kentang99";
    $dbname = "SYSTEM.XEPDB1";

    // Create connection
    $conn = new mysqli($dbhost, $dbuser, $dbpassword, $dbname);

    // Check connection
    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
    }

    // Get the form data
    if ($_SERVER["REQUEST_METHOD"] == "POST") {
        $name = $_POST['name'];
        $nameId = $_POST['nameId'];
        $action = $_POST['action'];

        if ($action == 'add') {
            // Prepare the SQL statement
            $stmt = $conn->prepare("INSERT INTO your_table (name) VALUES (?)");
            $stmt->bind_param("s", $name); // 's' specifies the variable type => 'string'
        } elseif ($action == 'update') {
            // Prepare the SQL statement for update
            $stmt = $conn->prepare("UPDATE your_table SET name = ? WHERE id = ?");
            $stmt->bind_param("si", $name, $nameId); // 'si' specifies the variable types => 'string', 'integer'
        } elseif ($action == 'delete') {
            // Prepare the SQL statement for delete
            $stmt = $conn->prepare("DELETE FROM your_table WHERE id = ?");
            $stmt->bind_param("i", $nameId); // 'i' specifies the variable type => 'integer'
        }

        // Execute the SQL statement
        $stmt->execute();
        // Close the connection
        $stmt->close();
    }

    $conn->close();
    ?>

    <label for="nameInput">Enter your name:</label><br>
    <input type="text" id="nameInput">
    <input type="hidden" id="nameId" name="nameId">
    <input type="hidden" id="action" name="action">
    <button onclick="addName()">Enter</button>
    <button onclick="editName()">Edit</button>
    <button onclick="deleteName()">Delete</button>
    <div id="nameList"></div>

    <script>
        var names = [];

        function addName() {
            var nameInput = document.getElementById('nameInput');
            var name = nameInput.value;
            if (name) {
                names.push(name);
                nameInput.value = '';
                updateNameList();
            }
        }

        function editName() {
            var nameListDiv = document.getElementById('nameList');
            var name = nameListDiv.querySelector('.selected');
            if (name) {
                var newName = prompt('Enter new name for ' + name.textContent);
                if (newName) {
                    names[names.indexOf(name.textContent)] = newName;
                    updateNameList();
                }
            }
        }

        function deleteName() {
            var nameListDiv = document.getElementById('nameList');
            var name = nameListDiv.querySelector('.selected');
            if (name) {
                names.splice(names.indexOf(name.textContent), 1);
                updateNameList();
            }
        }

        function updateNameList() {
            var nameListDiv = document.getElementById('nameList');
            nameListDiv.innerHTML = names.map(function(name) {
                return '<div onclick="selectName(this)">' + name + '</div>';
            }).join('');
        }

        function selectName(element) {
            var nameListDiv = document.getElementById('nameList');
            var selected = nameListDiv.querySelector('.selected');
            if (selected) {
                selected.classList.remove('selected');
            }
            element.classList.add('selected');
        }
    </script>
</body>
</html>
