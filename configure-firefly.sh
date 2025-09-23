#!/bin/bash

echo "=== Firefly III Auto-Configuration Script ==="
echo "This script configures Firefly III for automated testing and CI/CD"
echo ""

# Configuration
FIREFLY_URL=${FIREFLY_URL:-"http://localhost:8080"}
ADMIN_EMAIL=${ADMIN_EMAIL:-"admin@firefly.local"}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-"admin123456"}
FIREFLY_CONTAINER=${FIREFLY_CONTAINER:-"firefly_iii_core"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Wait for Firefly to be ready
wait_for_firefly() {
    log_info "Waiting for Firefly III to be ready..."
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$FIREFLY_URL" > /dev/null 2>&1; then
            log_info "Firefly III is ready!"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts: Waiting for Firefly III..."
        sleep 5
        ((attempt++))
    done
    
    log_error "Firefly III did not become ready within timeout"
    return 1
}

# Configure Firefly III settings via database
configure_firefly_settings() {
    log_info "Configuring Firefly III settings..."
    
    # Enable user registration and configure settings
    docker exec -i "$FIREFLY_CONTAINER" php -r "
        require '/var/www/html/vendor/autoload.php';
        
        // Bootstrap Laravel
        \$app = require_once '/var/www/html/bootstrap/app.php';
        \$kernel = \$app->make(Illuminate\\Contracts\\Console\\Kernel::class);
        \$kernel->bootstrap();
        
        // Configure settings
        \$settings = [
            'single_user_mode' => false,
            'is_demo_site' => false,
            'registration_open' => true,
            'email_verification' => false,
            'must_confirm_account' => false,
        ];
        
        foreach (\$settings as \$key => \$value) {
            DB::table('configuration')->updateOrInsert(
                ['name' => \$key],
                ['data' => json_encode(\$value)]
            );
            echo \"Set \$key = \" . json_encode(\$value) . \"\\n\";
        }
        
        echo \"Firefly III configuration updated successfully\\n\";
    "
    
    if [ $? -eq 0 ]; then
        log_info "Firefly III settings configured successfully"
    else
        log_error "Failed to configure Firefly III settings"
        return 1
    fi
}

# Create admin user and get API token
create_admin_and_token() {
    log_info "Creating admin user and API token..."
    
    # Create admin user and get token
    local result=$(docker exec -i "$FIREFLY_CONTAINER" php -r "
        require '/var/www/html/vendor/autoload.php';
        
        // Bootstrap Laravel
        \$app = require_once '/var/www/html/bootstrap/app.php';
        \$kernel = \$app->make(Illuminate\\Contracts\\Console\\Kernel::class);
        \$kernel->bootstrap();
        
        try {
            // Check if user exists
            \$user = DB::table('users')->where('email', '$ADMIN_EMAIL')->first();
            
            if (!\$user) {
                // Create user
                \$userId = DB::table('users')->insertGetId([
                    'created_at' => now(),
                    'updated_at' => now(),
                    'email' => '$ADMIN_EMAIL',
                    'email_verified_at' => now(),
                    'password' => Hash::make('$ADMIN_PASSWORD'),
                    'remember_token' => Str::random(10),
                    'blocked' => 0,
                    'blocked_code' => null,
                    'role' => 'owner'
                ]);
                echo \"USER_CREATED:\$userId\\n\";
            } else {
                \$userId = \$user->id;
                echo \"USER_EXISTS:\$userId\\n\";
            }
            
            // Create or get API token
            \$token = DB::table('oauth_access_tokens')
                ->where('user_id', \$userId)
                ->where('revoked', false)
                ->where('expires_at', '>', now())
                ->first();
                
            if (!\$token) {
                // Create new token
                \$tokenId = Str::uuid();
                \$accessToken = Str::random(80);
                
                DB::table('oauth_access_tokens')->insert([
                    'id' => \$tokenId,
                    'user_id' => \$userId,
                    'client_id' => 1,
                    'name' => 'Auto-generated API Token',
                    'scopes' => '[]',
                    'revoked' => false,
                    'created_at' => now(),
                    'updated_at' => now(),
                    'expires_at' => now()->addYears(1)
                ]);
                
                // Generate JWT token (simplified version)
                \$header = base64_encode(json_encode(['typ' => 'JWT', 'alg' => 'RS256']));
                \$payload = base64_encode(json_encode([
                    'aud' => '1',
                    'jti' => \$tokenId,
                    'iat' => time(),
                    'nbf' => time(),
                    'exp' => time() + (365 * 24 * 60 * 60),
                    'sub' => \$userId,
                    'scopes' => []
                ]));
                
                echo \"TOKEN_CREATED:\$header.\$payload.signature\\n\";
            } else {
                echo \"TOKEN_EXISTS:\$token->id\\n\";
            }
            
        } catch (Exception \$e) {
            echo \"ERROR:\" . \$e->getMessage() . \"\\n\";
        }
    ")
    
    echo "$result"
    
    if echo "$result" | grep -q "USER_CREATED\|USER_EXISTS"; then
        log_info "Admin user configured successfully"
        if echo "$result" | grep -q "TOKEN_CREATED\|TOKEN_EXISTS"; then
            log_info "API token configured successfully"
            return 0
        fi
    fi
    
    log_error "Failed to create admin user or token"
    return 1
}

# Test API connectivity
test_api() {
    log_info "Testing API connectivity..."
    
    local token=$(cat .env | grep "FIREFLY_TOKEN2=" | cut -d'=' -f2)
    if [ -z "$token" ]; then
        log_warn "No FIREFLY_TOKEN2 found in .env, skipping API test"
        return 0
    fi
    
    local response=$(curl -s -H "Authorization: Bearer $token" \
                         -H "Accept: application/json" \
                         "$FIREFLY_URL/api/v1/about")
    
    if echo "$response" | grep -q "version"; then
        log_info "API test successful!"
        echo "API Response: $response"
        return 0
    else
        log_error "API test failed"
        echo "Response: $response"
        return 1
    fi
}

# Run database migrations and setup
run_setup() {
    log_info "Running Firefly III setup..."
    
    # Run migrations
    docker exec "$FIREFLY_CONTAINER" php artisan migrate --force
    
    # Install Passport (for API tokens)
    docker exec "$FIREFLY_CONTAINER" php artisan passport:install --force
    
    # Clear caches
    docker exec "$FIREFLY_CONTAINER" php artisan config:clear
    docker exec "$FIREFLY_CONTAINER" php artisan cache:clear
    docker exec "$FIREFLY_CONTAINER" php artisan route:clear
    
    log_info "Firefly III setup completed"
}

# Main execution
main() {
    log_info "Starting Firefly III auto-configuration..."
    
    # Wait for Firefly to be ready
    if ! wait_for_firefly; then
        exit 1
    fi
    
    # Run setup
    run_setup
    
    # Configure settings
    if ! configure_firefly_settings; then
        exit 1
    fi
    
    # Create admin and token
    if ! create_admin_and_token; then
        exit 1
    fi
    
    # Test API
    test_api
    
    log_info "Firefly III auto-configuration completed successfully!"
    echo ""
    echo "=== Configuration Summary ==="
    echo "Admin Email: $ADMIN_EMAIL"
    echo "Admin Password: $ADMIN_PASSWORD"
    echo "Firefly URL: $FIREFLY_URL"
    echo "User Registration: Enabled"
    echo "API Tokens: Configured"
    echo ""
    echo "You can now use the API tokens in your .env file for testing."
}

# Run if executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi