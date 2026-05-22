#!/usr/bin/env bash
# ============================================================================
# Genius Loci — Demo Launcher
# ============================================================================
# Запускает сервер (FastAPI), фронтенд (React) и симуляцию роботов
# параллельно. По Ctrl+C — корректно завершает все процессы.
#
# Использование:
#   ./demo.sh                    # Запуск с настройками по умолчанию
#   ./demo.sh --robots 5         # 5 роботов в симуляции
#   ./demo.sh --duration 120     # Остановить симуляцию через 120 секунд
#   ./demo.sh --no-sim           # Только сервер + фронтенд
#   ./demo.sh --build            # Собрать фронтенд перед запуском
# ============================================================================

set -e

# ─── Параметры по умолчанию ────────────────────────────────────────────────
ROBOT_COUNT=3
SIM_DURATION=300       # 0 = бесконечно
NO_SIM=false
BUILD=false
SERVER_PORT=8000
FRONTEND_PORT=5173

# ─── Цвета для вывода ──────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ─── Парсинг аргументов ────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --robots)
            ROBOT_COUNT="$2"; shift 2 ;;
        --duration)
            SIM_DURATION="$2"; shift 2 ;;
        --no-sim)
            NO_SIM=true; shift ;;
        --build)
            BUILD=true; shift ;;
        --server-port)
            SERVER_PORT="$2"; shift 2 ;;
        --frontend-port)
            FRONTEND_PORT="$2"; shift 2 ;;
        --help|-h)
            echo "Genius Loci Demo Launcher"
            echo ""
            echo "Usage: ./demo.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --robots N        Number of simulated robots (default: 3)"
            echo "  --duration S      Simulation duration in seconds, 0=infinite (default: 300)"
            echo "  --no-sim          Start only server + frontend"
            echo "  --build           Build frontend before starting"
            echo "  --server-port P   Backend port (default: 8000)"
            echo "  --frontend-port P Frontend port (default: 5173)"
            echo "  --help, -h        Show this help"
            exit 0 ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1 ;;
    esac
done

# ─── Пути ───────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GENOMEOS_DIR="$SCRIPT_DIR/GenomeOS"
SERVER_DIR="$SCRIPT_DIR/Server/backend"
FRONTEND_DIR="$SCRIPT_DIR/Server/frontend"
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/.pids"

# ─── Флаги состояния ───────────────────────────────────────────────────────
SERVER_READY=false
FRONTEND_READY=false
CLEANUP_DONE=false

# ─── Очистка при выходе ────────────────────────────────────────────────────
cleanup() {
    if $CLEANUP_DONE; then return; fi
    CLEANUP_DONE=true

    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  Shutting down all services...${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Останавливаем процессы в обратном порядке
    for pid_file in "$PID_DIR"/sim.pid "$PID_DIR"/frontend.pid "$PID_DIR"/server.pid; do
        if [[ -f "$pid_file" ]]; then
            local pid
            pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                # Отправляем сигнал группе процессов
                kill -TERM -- -"$(ps -o pgid= -p "$pid" | tr -d ' ')" 2>/dev/null || true
                kill -TERM "$pid" 2>/dev/null || true
                # Ждём завершения
                for i in {1..10}; do
                    if ! kill -0 "$pid" 2>/dev/null; then break; fi
                    sleep 0.2
                done
                # Принудительно
                kill -KILL "$pid" 2>/dev/null || true
            fi
            rm -f "$pid_file"
        fi
    done

    rm -rf "$PID_DIR"
    echo -e "${GREEN}  All services stopped.${NC}"
}

trap cleanup EXIT INT TERM

# ─── Подготовка ────────────────────────────────────────────────────────────
mkdir -p "$LOG_DIR" "$PID_DIR"

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         Genius Loci — Warehouse Robot Fleet Demo             ║${NC}"
echo -e "${CYAN}╠═══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║  Robots:    ${ROBOT_COUNT}                                               ║${NC}"
echo -e "${CYAN}║  Duration:  ${SIM_DURATION}s                                              ║${NC}"
echo -e "${CYAN}║  Backend:   http://localhost:${SERVER_PORT}                           ║${NC}"
echo -e "${CYAN}║  Frontend:  http://localhost:${FRONTEND_PORT}                          ║${NC}"
echo -e "${CYAN}║  Swagger:   http://localhost:${SERVER_PORT}/docs                       ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Проверка зависимостей ────────────────────────────────────────────────
check_dependency() {
    if ! command -v "$1" &>/dev/null; then
        echo -e "${RED}✗ $1 не найден. Установите $1 для продолжения.${NC}"
        exit 1
    fi
}

echo -e "${BLUE}[check]${NC} Checking dependencies..."
check_dependency python3
check_dependency node
check_dependency npm

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
NODE_VERSION=$(node --version 2>&1)
echo -e "       Python: ${GREEN}$PYTHON_VERSION${NC}"
echo -e "       Node:   ${GREEN}$NODE_VERSION${NC}"
echo ""

# ─── Установка Python-зависимостей (если нужно) ────────────────────────────
install_python_deps() {
    local dir="$1"
    local name="$2"
    local req="$dir/requirements.txt"
    local venv="$dir/.venv"
    local hash_file="$dir/.venv/.req_hash"

    if [[ ! -f "$req" ]]; then
        echo -e "${YELLOW}[warn]${NC} $name: requirements.txt не найден, пропускаем"
        return
    fi

    # Создаём venv если нет
    if [[ ! -d "$venv" ]]; then
        echo -e "${BLUE}[venv]${NC} Creating virtual environment for $name..."
        python3 -m venv "$venv"
    fi

    # Проверяем, изменились ли зависимости (по хешу)
    local current_hash
    current_hash=$(md5sum "$req" | awk '{print $1}')
    local cached_hash
    cached_hash=$(cat "$hash_file" 2>/dev/null || echo "")

    if [[ "$current_hash" == "$cached_hash" ]]; then
        echo -e "       ${GREEN}✓${NC} $name dependencies already installed"
        return
    fi

    echo -e "${BLUE}[install]${NC} Installing $name dependencies..."
    "$venv/bin/pip" install -q -r "$req" 2>&1 | tail -3
    echo "$current_hash" > "$hash_file"
    echo -e "       ${GREEN}✓${NC} $name dependencies installed"
}

install_python_deps "$SERVER_DIR" "Server"
install_python_deps "$GENOMEOS_DIR" "GenomeOS"

# ─── Установка npm-зависимостей ────────────────────────────────────────────
if [[ ! -f "$FRONTEND_DIR/node_modules/.bin/vite" ]] || [[ ! -d "$FRONTEND_DIR/node_modules/tailwindcss" ]]; then
    # Удаляем возможно битые node_modules
    if [[ -d "$FRONTEND_DIR/node_modules" ]]; then
        echo -e "${YELLOW}[clean]${NC} Removing stale node_modules..."
        rm -rf "$FRONTEND_DIR/node_modules"
    fi
    echo -e "${BLUE}[install]${NC} Installing frontend dependencies..."
    (cd "$FRONTEND_DIR" && npm install --no-audit --no-fund)
    echo -e "       ${GREEN}✓${NC} Frontend dependencies installed"
else
    echo -e "       ${GREEN}✓${NC} Frontend dependencies already installed"
fi

# ─── Сборка фронтенда (опционально) ────────────────────────────────────────
if $BUILD; then
    echo -e "${BLUE}[build]${NC} Building frontend..."

    # Убедимся, что TypeScript установлен
    if [[ ! -d "$FRONTEND_DIR/node_modules/typescript" ]]; then
        echo -e "       Installing TypeScript..."
        (cd "$FRONTEND_DIR" && npm install --no-audit --no-fund)
    fi

    # Используем локальный tsc из node_modules
    (cd "$FRONTEND_DIR" && ./node_modules/.bin/tsc --noEmit && ./node_modules/.bin/vite build)
    echo -e "       ${GREEN}✓${NC} Frontend built"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════════
# ЗАПУСК СЕРВИСОВ
# ═══════════════════════════════════════════════════════════════════════════

# ─── 1. Сервер (FastAPI) ───────────────────────────────────────────────────
echo -e "${BLUE}[1/3]${NC} Starting ${GREEN}Backend Server${NC}..."
cd "$SERVER_DIR"
"$SERVER_DIR/.venv/bin/python3" main.py > "$LOG_DIR/server.log" 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > "$PID_DIR/server.pid"

# Ждём готовности сервера
echo -ne "       Waiting for server "
for i in {1..30}; do
    if curl -s "http://localhost:$SERVER_PORT/health" &>/dev/null; then
        echo -e " ${GREEN}ready${NC}"
        SERVER_READY=true
        break
    fi
    echo -n "."
    sleep 0.5
done

if ! $SERVER_READY; then
    echo -e " ${RED}FAILED${NC}"
    echo -e "${RED}✗ Server failed to start. Check logs: $LOG_DIR/server.log${NC}"
    tail -20 "$LOG_DIR/server.log"
    exit 1
fi

# ─── 2. Фронтенд (React/Vite) ──────────────────────────────────────────────
echo -e "${BLUE}[2/3]${NC} Starting ${GREEN}Frontend (React)${NC}..."
cd "$FRONTEND_DIR"
./node_modules/.bin/vite --port "$FRONTEND_PORT" > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$PID_DIR/frontend.pid"

echo -ne "       Waiting for frontend "
for i in {1..30}; do
    if curl -s "http://localhost:$FRONTEND_PORT" &>/dev/null; then
        echo -e " ${GREEN}ready${NC}"
        FRONTEND_READY=true
        break
    fi
    echo -n "."
    sleep 0.5
done

if ! $FRONTEND_READY; then
    echo -e " ${YELLOW}timeout${NC} (Vite may still be starting, continuing anyway)"
fi

# ─── 3. Симуляция роботов ──────────────────────────────────────────────────
if $NO_SIM; then
    echo -e "${BLUE}[3/3]${NC} ${YELLOW}Simulation skipped (--no-sim)${NC}"
else
    echo -e "${BLUE}[3/3]${NC} Starting ${GREEN}Robot Simulation${NC} (${ROBOT_COUNT} robots)..."
    cd "$GENOMEOS_DIR"

    if [[ "$SIM_DURATION" -eq 0 ]]; then
        DURATION_ARG=""
    else
        DURATION_ARG="--duration $SIM_DURATION"
    fi

    "$GENOMEOS_DIR/.venv/bin/python3" -m simulation.multi_robot_sim \
        --count "$ROBOT_COUNT" \
        $DURATION_ARG \
        --server "ws://localhost:$SERVER_PORT" \
        > "$LOG_DIR/simulation.log" 2>&1 &
    SIM_PID=$!
    echo "$SIM_PID" > "$PID_DIR/sim.pid"

    sleep 2
    if kill -0 "$SIM_PID" 2>/dev/null; then
        echo -e "       ${GREEN}✓${NC} Simulation running (PID: $SIM_PID)"
    else
        echo -e "       ${YELLOW}⚠${NC}  Simulation may have exited early"
    fi
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  All services are running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${CYAN}Frontend:${NC}  http://localhost:$FRONTEND_PORT"
echo -e "  ${CYAN}Backend:${NC}   http://localhost:$SERVER_PORT"
echo -e "  ${CYAN}Swagger:${NC}   http://localhost:$SERVER_PORT/docs"
echo -e "  ${CYAN}Health:${NC}    http://localhost:$SERVER_PORT/health"
echo ""
echo -e "  ${CYAN}Demo accounts:${NC}"
echo -e "    admin    / admin"
echo -e "    operator / operator"
echo ""
echo -e "  ${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# ─── Мониторинг ────────────────────────────────────────────────────────────
# Раз в 10 секунд проверяем живость процессов
MONITOR_INTERVAL=10
while true; do
    sleep "$MONITOR_INTERVAL"

    # Проверка сервера
    if [[ -f "$PID_DIR/server.pid" ]]; then
        pid=$(cat "$PID_DIR/server.pid")
        if ! kill -0 "$pid" 2>/dev/null; then
            echo -e "${RED}[$(date +%H:%M:%S)] Server crashed! Check $LOG_DIR/server.log${NC}"
        fi
    fi

    # Проверка симуляции
    if [[ -f "$PID_DIR/sim.pid" ]]; then
        pid=$(cat "$PID_DIR/sim.pid")
        if ! kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}[$(date +%H:%M:%S)] Simulation finished.${NC}"
            rm -f "$PID_DIR/sim.pid"
            if [[ "$SIM_DURATION" -ne 0 ]]; then
                echo -e "${CYAN}  Server and frontend are still running. Press Ctrl+C to stop.${NC}"
            fi
        fi
    fi
done
