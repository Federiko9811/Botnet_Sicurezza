### Progetto Botnet

Realizzato da: *Federico Raponi*

### Nota

Prima di poter eseguire il codice è necessario installare le librerie necessarie tramite il comando:

    pip install -r requirements.txt

Il funzionamento di questo codice prevede che il C&C sia in esecuzione su una Macchina Virtuale con IP
statico `10.0.2.15`, mentre i bot devono essere eseguiti su altre macchine virtuali che si connettono al C&C
tramite la rete locale NAT.

Il C&C esporrà la porta `15200` in attesa della connessione dei bot. Per eseguire il C&C è necessario eseguire il comando:

    python3 CC.py

Per eseguire i bot è necessario eseguire il comando:
    
    python3 Bot.py

### Descrizione

Questa botnet è stata realizzata per il progetto del corso di Sicurezza Informatica dell'Università La Sapienza di Roma.

