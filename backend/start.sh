#!/bin/bash
# 启动脚本 - 支持开发和生产环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Python环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 not found. Please install Python 3.7+"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_info "Using Python $python_version"
}

# 检查并安装依赖
install_dependencies() {
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi
    
    print_info "Installing dependencies..."
    pip3 install -r requirements.txt
}

# 开发环境启动
start_dev() {
    print_info "Starting in development mode..."
    export FLASK_ENV=development
    export FLASK_DEBUG=1
    python3 app.py
}

# 生产环境启动
start_prod() {
    print_info "Starting in production mode with Gunicorn..."
    
    # 检查Gunicorn是否安装
    if ! command -v gunicorn &> /dev/null; then
        print_error "Gunicorn not found. Installing..."
        pip3 install gunicorn
    fi
    
    # 设置环境变量
    export FLASK_ENV=production
    export FLASK_DEBUG=0
    
    # 启动Gunicorn
    gunicorn --config gunicorn_config.py app:app
}

# 健康检查
health_check() {
    local port=${1:-5001}
    local max_attempts=30
    local attempt=1
    
    print_info "Performing health check on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
            print_info "Health check passed!"
            return 0
        fi
        
        print_warn "Health check attempt $attempt/$max_attempts failed, retrying in 2s..."
        sleep 2
        ((attempt++))
    done
    
    print_error "Health check failed after $max_attempts attempts"
    return 1
}

# 显示帮助信息
show_help() {
    echo "Usage: $0 [OPTION]"
    echo "Start the Shenlun backend application"
    echo ""
    echo "Options:"
    echo "  dev, development    Start in development mode (default)"
    echo "  prod, production    Start in production mode with Gunicorn"
    echo "  install             Install dependencies only"
    echo "  health [PORT]       Perform health check (default port: 5001)"
    echo "  help, -h, --help    Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  PORT                Server port (default: 5001)"
    echo "  GUNICORN_WORKERS    Number of Gunicorn workers"
    echo "  LOG_LEVEL           Logging level (DEBUG, INFO, WARNING, ERROR)"
    echo "  MAX_CONCURRENT_REQUESTS  Maximum concurrent requests (default: 10)"
    echo "  RATE_LIMIT_PER_MINUTE    Rate limit per minute (default: 60)"
}

# 主逻辑
main() {
    local mode=${1:-dev}
    
    case $mode in
        "dev"|"development")
            check_python
            start_dev
            ;;
        "prod"|"production")
            check_python
            start_prod
            ;;
        "install")
            check_python
            install_dependencies
            ;;
        "health")
            health_check $2
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown option: $mode"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"