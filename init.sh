echo 'Iniciando os trabalhos...'
echo 'Verificando se está ouvindo algo...'
python3 update.py >/dev/null 2>&1

echo 'Dormindo por dois minutos...'
while true;
    do sleep 120
    echo 'Verificando se está ouvindo algo...'
    python3 update.py >/dev/null 2>&1
    echo 'Dormindo por dois minutos...'
done
