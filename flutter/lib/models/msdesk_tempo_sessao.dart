// MSUPTECH_MSDESK_TEMPO_SESSAO_V1: "quem acessa escolhe quanto tempo vai ficar: hoje vou trabalhar 1 hora
// nessa maquina e depois o acesso fecha ou fica em stand-by" (Marcus 28/10). AnyDesk/TeamViewer nao tem.
// Fica so do lado de quem ACESSA (tecnico), por sessao: nada muda no computador acessado.
//  - Faltando 5 min: aviso com "mais 30 min".
//  - Acabou + "Encerrar": fecha a conexao.
//  - Acabou + "Stand-by": a tela remota fica coberta e o controle parado; "Voltar" retoma (sem pedir senha
//    por ate 30 min, ver MSUPTECH_MSDESK_RECONEXAO_V1). Sem resposta em 30 min, encerra.
//  - "Bloquear o computador" (opcional): tranca o Windows remoto quando o tempo acaba.
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../common.dart';
import 'model.dart';
import 'platform_model.dart';

enum MsdeskFimSessao { encerrar, standby }

class MsdeskTempoSessao {
  static final _porSessao = <String, MsdeskTempoSessao>{};

  static MsdeskTempoSessao de(FFI ffi) => _porSessao.putIfAbsent(
      ffi.sessionId.toString(), () => MsdeskTempoSessao._(ffi));

  static MsdeskTempoSessao? daSessao(SessionID sessionId) =>
      _porSessao[sessionId.toString()];

  MsdeskTempoSessao._(this.ffi);

  static const _tagAviso = 'msdesk-tempo-aviso';
  static const _tagStandby = 'msdesk-tempo-standby';
  static const _standbyMaximo = Duration(minutes: 30);

  final FFI ffi;
  final restante = Rxn<Duration>();
  final emStandby = false.obs;
  MsdeskFimSessao fim = MsdeskFimSessao.encerrar;
  bool bloquear = false;

  DateTime? _termina;
  DateTime? _standbyDesde;
  Timer? _relogio;
  bool _avisou = false;
  bool _caiuNoStandby = false;

  bool get ativo => _termina != null || emStandby.value;

  void iniciar(Duration duracao, MsdeskFimSessao fim, bool bloquear) {
    this.fim = fim;
    this.bloquear = bloquear;
    _termina = DateTime.now().add(duracao);
    _avisou = false;
    _relogio?.cancel();
    _relogio = Timer.periodic(const Duration(seconds: 1), (_) => _tique());
    _tique();
  }

  void estender(Duration mais) {
    final base = (_termina != null && _termina!.isAfter(DateTime.now()))
        ? _termina!
        : DateTime.now();
    _termina = base.add(mais);
    _avisou = false;
    ffi.dialogManager.dismissByTag(_tagAviso);
    _tique();
  }

  void cancelar() {
    _relogio?.cancel();
    _relogio = null;
    _termina = null;
    _standbyDesde = null;
    restante.value = null;
    emStandby.value = false;
    ffi.dialogManager.dismissByTag(_tagAviso);
    ffi.dialogManager.dismissByTag(_tagStandby);
  }

  /// Enquanto esta em stand-by, uma queda (ex.: o computador remoto desliga por inatividade)
  /// nao fecha a aba: fica guardada para o "Voltar" reconectar.
  bool engolirQuedaNoStandby(String title) {
    if (!emStandby.value || title != 'Connection Error') return false;
    _caiuNoStandby = true;
    return true;
  }

  void _tique() {
    if (ffi.closed) {
      cancelar();
      _porSessao.remove(ffi.sessionId.toString());
      return;
    }
    if (emStandby.value) {
      if (_standbyDesde != null &&
          DateTime.now().difference(_standbyDesde!) > _standbyMaximo) {
        _encerrar();
      }
      return;
    }
    if (_termina == null) return;
    final falta = _termina!.difference(DateTime.now());
    restante.value = falta.isNegative ? Duration.zero : falta;
    if (!_avisou && falta <= const Duration(minutes: 5) && falta.inSeconds > 0) {
      _avisou = true;
      _mostrarAviso();
    }
    if (falta.inSeconds <= 0) {
      _acabou();
    }
  }

  void _mostrarAviso() {
    ffi.dialogManager.show(tag: _tagAviso, (setState, close, context) {
      return CustomAlertDialog(
        title: const Text('Faltam 5 minutos'),
        content: Text(fim == MsdeskFimSessao.encerrar
            ? 'O tempo que você escolheu para esta sessão está acabando. Depois a conexão será encerrada.'
            : 'O tempo que você escolheu para esta sessão está acabando. Depois ela fica em stand-by.'),
        actions: [
          dialogButton('Ok', onPressed: close, isOutline: true),
          dialogButton('Mais 30 min',
              onPressed: () => estender(const Duration(minutes: 30))),
        ],
        onSubmit: close,
        onCancel: close,
      );
    });
  }

  void _acabou() {
    _termina = null;
    restante.value = null;
    ffi.dialogManager.dismissByTag(_tagAviso);
    if (bloquear) {
      bind.sessionLockScreen(sessionId: ffi.sessionId);
    }
    if (fim == MsdeskFimSessao.encerrar) {
      // Da tempo do bloqueio chegar ao outro lado antes de fechar.
      Timer(Duration(seconds: bloquear ? 2 : 0), _encerrar);
    } else {
      _entrarStandby();
    }
  }

  void _encerrar() {
    final id = ffi.id;
    cancelar();
    closeConnection(id: id);
  }

  void _entrarStandby() {
    emStandby.value = true;
    _standbyDesde = DateTime.now();
    _caiuNoStandby = false;
    ffi.inputModel.setRelativeMouseMode(false);
    ffi.dialogManager.show(tag: _tagStandby, (setState, close, context) {
      return CustomAlertDialog(
        title: const Text('Sessão em stand-by'),
        content: Text(
            'O tempo que você escolheu acabou. O controle deste computador está parado.\n\n'
            'Clique em "Voltar" para continuar (mais 30 min) ou em "Encerrar".'
            '${bloquear ? '\n\nO computador remoto foi bloqueado.' : ''}'),
        actions: [
          dialogButton('Encerrar', onPressed: _encerrar, isOutline: true),
          dialogButton('Voltar (+30 min)', onPressed: _voltar),
        ],
      );
    });
  }

  void _voltar() {
    final caiu = _caiuNoStandby;
    emStandby.value = false;
    _standbyDesde = null;
    _caiuNoStandby = false;
    ffi.dialogManager.dismissByTag(_tagStandby);
    iniciar(const Duration(minutes: 30), fim, bloquear);
    if (caiu) {
      ffi.ffiModel.reconnect(ffi.dialogManager, ffi.sessionId, false);
    }
  }
}

String msdeskRelogio(Duration d) {
  final h = d.inHours;
  final m = d.inMinutes.remainder(60).toString().padLeft(2, '0');
  final s = d.inSeconds.remainder(60).toString().padLeft(2, '0');
  return h > 0 ? '$h:$m:$s' : '$m:$s';
}

/// Janela "Tempo de sessão": escolher quanto tempo e o que acontece no fim.
void msdeskEscolherTempoSessao(FFI ffi) {
  final tempo = MsdeskTempoSessao.de(ffi);
  const opcoes = <String, int>{
    '30 min': 30,
    '1 hora': 60,
    '2 horas': 120,
    '4 horas': 240,
    '8 horas': 480,
  };
  var minutos = 60;
  var fim = tempo.fim;
  var bloquear = tempo.bloquear;
  ffi.dialogManager.show((setState, close, context) {
    void comecar() {
      tempo.iniciar(Duration(minutes: minutos), fim, bloquear);
      close();
    }

    return CustomAlertDialog(
      title: const Text('Tempo de sessão'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (tempo.ativo && tempo.restante.value != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(
                  'Faltam ${msdeskRelogio(tempo.restante.value!)}. Escolha um novo tempo ou desligue.',
                  style: const TextStyle(fontWeight: FontWeight.bold)),
            ),
          const Text('Quanto tempo você vai trabalhar nesta máquina?'),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: opcoes.entries
                .map((e) => ChoiceChip(
                      label: Text(e.key),
                      selected: minutos == e.value,
                      onSelected: (_) => setState(() => minutos = e.value),
                    ))
                .toList(),
          ),
          const SizedBox(height: 16),
          const Text('Quando o tempo acabar:'),
          RadioListTile<MsdeskFimSessao>(
            dense: true,
            contentPadding: EdgeInsets.zero,
            title: const Text('Encerrar a conexão'),
            value: MsdeskFimSessao.encerrar,
            groupValue: fim,
            onChanged: (v) => setState(() => fim = v!),
          ),
          RadioListTile<MsdeskFimSessao>(
            dense: true,
            contentPadding: EdgeInsets.zero,
            title: const Text('Ficar em stand-by (volto com um clique)'),
            value: MsdeskFimSessao.standby,
            groupValue: fim,
            onChanged: (v) => setState(() => fim = v!),
          ),
          CheckboxListTile(
            dense: true,
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            title: const Text('Bloquear o computador remoto no fim'),
            value: bloquear,
            onChanged: (v) => setState(() => bloquear = v ?? false),
          ),
          const SizedBox(height: 4),
          const Text('Faltando 5 minutos, o MS Desk avisa e você pode pedir mais tempo.',
              style: TextStyle(fontSize: 12)),
        ],
      ),
      actions: [
        if (tempo.ativo)
          dialogButton('Desligar o tempo', isOutline: true, onPressed: () {
            tempo.cancelar();
            close();
          }),
        dialogButton('Cancelar', onPressed: close, isOutline: true),
        dialogButton('Começar', onPressed: comecar),
      ],
      onSubmit: comecar,
      onCancel: close,
    );
  });
}
