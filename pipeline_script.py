import sys
import os
import traceback
from subprocess import Popen, PIPE
from Bio import SeqIO
import shutil

"""
usage: python pipeline_script.py INPUT.fasta  
"""

# ==========================================
# 路徑設定
# ==========================================
S4PRED_SCRIPT = '/opt/tools/s4pred/run_model.py'
HHSEARCH_BIN = '/opt/tools/hh-suite/build/bin/hhsearch'
HHDB_PATH = '/data/pdb70/pdb70'
# ==========================================

def run_parser(hhr_file):
    cmd = ['python3', './results_parser.py', hhr_file]
    p = Popen(cmd, stdin=PIPE,stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    print(out.decode("utf-8", errors='ignore'))
    if err:
        print(f"Parser Error: {err.decode('utf-8', errors='ignore')}")

def run_hhsearch(a3m_file):
    cmd = [HHSEARCH_BIN, '-i', a3m_file, '-cpu', '1', '-d', HHDB_PATH]
    p = Popen(cmd, stdin=PIPE,stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        print(f"HHSearch Failed: {err.decode('utf-8', errors='ignore')}")

def read_horiz(tmp_file, horiz_file, a3m_file):
    pred = ''
    conf = ''
    with open(horiz_file) as fh_in:
        for line in fh_in:
            if line.startswith('Conf: '):
                conf += line[6:].rstrip()
            if line.startswith('Pred: '):
                pred += line[6:].rstrip()
    with open(tmp_file) as fh_in:
        contents = fh_in.read()
    with open(a3m_file, "w") as fh_out:
        fh_out.write(f">ss_pred\n{pred}\n>ss_conf\n{conf}\n")
        fh_out.write(contents)

def run_s4pred(input_file, out_file):
    cmd = ['python3', S4PRED_SCRIPT, '-t', 'horiz', '-T', '1', input_file]
    p = Popen(cmd, stdin=PIPE,stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    if p.returncode == 0:
        with open(out_file, "w") as fh_out:
            fh_out.write(out.decode("utf-8", errors='ignore'))
    else:
        raise Exception(f"S4Pred failed: {err.decode('utf-8', errors='ignore')}")

def read_input(file):
    print("READING FASTA FILES")
    sequences = {}
    for record in SeqIO.parse(file, "fasta"):
        sequences[record.id] = record.seq
    return(sequences)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 pipeline_script.py <input_fasta>")
        sys.exit(1)

    sequences = read_input(sys.argv[1])
    tmp_file = "tmp.fas"
    horiz_file = "tmp.horiz"
    a3m_file = "tmp.a3m"
    hhr_file = "tmp.hhr"
    
    for k, v in sequences.items():
        # ★★★【續傳機制】檢查是否已完成 ★★★
        final_output = f'{k}_parse.out'
        if os.path.exists(final_output):
            # 如果檔案已經存在，直接跳過，不印訊息以免 Log 爆炸
            continue 

        print(f'Now analysing input: {k}')
        
        # ★★★【防護網】★★★
        try:
            with open(tmp_file, "w") as fh_out:
                fh_out.write(f">{k}\n")
                fh_out.write(f"{v}\n")
            
            run_s4pred(tmp_file, horiz_file)
            read_horiz(tmp_file, horiz_file, a3m_file)
            run_hhsearch(a3m_file)
            run_parser(hhr_file)
            
            if os.path.exists("hhr_parse.out"):
                shutil.move("hhr_parse.out", final_output)
            else:
                print(f"Warning: Analysis for {k} did not generate output.")

        except Exception as e:
            print(f"CRITICAL ERROR processing sequence {k}: {e}")
            traceback.print_exc()
            print(">>> SKIPPING THIS SEQUENCE <<<")
            continue