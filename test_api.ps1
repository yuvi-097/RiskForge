$ErrorActionPreference = "Stop"

Write-Host "--- RiskForge API Test (PowerShell) ---"

# 1. Health Check
Write-Host "`n1. Checking Health..."
try {
    $health = Invoke-RestMethod -Uri http://127.0.0.1:8080/health -Method GET
    Write-Host "   Status: $($health.status)"
    Write-Host "   Services: $($health.services | ConvertTo-Json -Depth 1 -Compress)"
} catch {
    Write-Error "Health check failed: $_"
    exit 1
}

# 2. Register User (random ID to avoid duplicates)
$rnd = Get-Random -Minimum 1000 -Maximum 9999
$email = "user$rnd@example.com"
$password = "SecurePass123"

Write-Host "`n2. Registering new user '$email'..."
try {
    $registerBody = @{
        email = $email
        password = $password
    } | ConvertTo-Json
    
    $user = Invoke-RestMethod -Uri http://127.0.0.1:8080/api/v1/auth/register `
        -Method POST `
        -Body $registerBody `
        -ContentType 'application/json'
    
    Write-Host "   Success! User ID: $($user.id)"
} catch {
    Write-Error "Registration failed: $_"
    exit 1
}

# 3. Login
Write-Host "`n3. Logging in..."
try {
    $loginBody = "username=$email&password=$password"
    
    $login = Invoke-RestMethod -Uri http://127.0.0.1:8080/api/v1/auth/login `
        -Method POST `
        -Body $loginBody `
        -ContentType 'application/x-www-form-urlencoded'
    
    $token = $login.access_token
    Write-Host "   Login successful. Token acquired."
} catch {
    Write-Error "Login failed: $_"
    exit 1
}

# 4. Create Transaction
Write-Host "`n4. Creating Transaction..."
try {
    $headers = @{Authorization="Bearer $token"}
    $txnBody = @{
        amount = 150.0
        currency = "USD"
        location = "New York, NY"
        device_id = "powershell-client"
        ip_address = "127.0.0.1"
        transaction_time = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    } | ConvertTo-Json

    $txn = Invoke-RestMethod -Uri http://127.0.0.1:8080/api/v1/transactions/ `
        -Method POST `
        -Headers $headers `
        -Body $txnBody `
        -ContentType 'application/json'

    Write-Host "   Transaction Created!"
    Write-Host "   ID: $($txn.id)"
    Write-Host "   Status: $($txn.status)"
} catch {
    Write-Error "Transaction creation failed: $_"
    exit 1
}

Write-Host "`n--- Test Complete ---"
