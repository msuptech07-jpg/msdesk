// MSUPTECH_MSDESK_LICENCA_V1 (20/10/2026): licenca do MS Desk ("nao pagou, nao usa"; 7 dias de teste).
// O programa pede ao servidor de licencas da MSuptech uma licenca curta (48 h) para o proprio ID, ao abrir e a cada
// 6 h, e guarda em "msdesk-licenca". A licenca vai junto em cada pedido de conexao (src/ui_session_interface.rs) e o
// servidor de conexao confere. A faixa mostra o teste/assinatura e o atalho para assinar.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';

import 'models/platform_model.dart';

class MsdeskLicenca {
  static final estado = ''.obs; // teste | ativo | vencido
  static final dias = 0.obs;
  static final plano = ''.obs;
  static final assinar = 'https://acesso.msuptech.com.br/assinar'.obs;
  static Timer? _relogio;

  static void iniciar() {
    atualizar();
    _relogio ??= Timer.periodic(const Duration(hours: 6), (_) => atualizar());
  }

  static Future<void> atualizar() async {
    try {
      final id = await bind.mainGetMyId();
      if (id.isEmpty) {
        Future.delayed(const Duration(seconds: 5), atualizar);
        return;
      }
      final uri = Uri.https('acesso.msuptech.com.br', '/licenca/api/licenca', {
        'id': id,
        'so': Platform.operatingSystem,
        'v': await bind.mainGetVersion(),
      });
      final r = await http.get(uri).timeout(const Duration(seconds: 20));
      if (r.statusCode != 200) return;
      final j = jsonDecode(r.body) as Map<String, dynamic>;
      estado.value = (j['estado'] ?? '').toString();
      dias.value = (j['dias'] ?? 0) as int;
      plano.value = (j['plano'] ?? '').toString();
      if (j['assinar'] != null) assinar.value = j['assinar'].toString();
      await bind.mainSetLocalOption(
          key: 'msdesk-licenca', value: (j['licenca'] ?? '').toString());
    } catch (_) {
      // sem internet: tenta de novo em 1 minuto (a licenca guardada vale 48 h)
      Future.delayed(const Duration(minutes: 1), atualizar);
    }
  }

  static void abrirAssinatura() {
    launchUrl(Uri.parse(assinar.value), mode: LaunchMode.externalApplication);
  }
}

/// Faixa da tela inicial: "Teste gratis: faltam X dias - Assinar" / "Assinatura ativa" / "Seu teste acabou".
class MsdeskLicencaFaixa extends StatelessWidget {
  const MsdeskLicencaFaixa({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Obx(() {
      final e = MsdeskLicenca.estado.value;
      if (e.isEmpty || MsdeskLicenca.plano.value == 'cortesia') {
        return const SizedBox.shrink();
      }
      final vencido = e == 'vencido';
      final d = MsdeskLicenca.dias.value;
      final texto = vencido
          ? 'Seu teste do MS Desk acabou'
          : e == 'teste'
              ? 'Teste grátis: ${d <= 1 ? 'último dia' : 'faltam $d dias'}'
              : 'Assinatura ativa · ${d <= 1 ? 'vence hoje' : '$d dias'}';
      final cor = vencido ? const Color(0xFFB3261E) : const Color(0xFF22324F);
      return Container(
        margin: const EdgeInsets.fromLTRB(10, 8, 10, 4),
        padding: const EdgeInsets.fromLTRB(12, 8, 6, 8),
        decoration: BoxDecoration(
          color: cor.withOpacity(0.08),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: cor.withOpacity(0.35)),
        ),
        child: Row(children: [
          Expanded(
              child: Text(texto,
                  style: TextStyle(
                      fontSize: 13, fontWeight: FontWeight.w600, color: cor))),
          if (e != 'ativo' || d <= 7)
            TextButton(
              onPressed: MsdeskLicenca.abrirAssinatura,
              child: Text(e == 'ativo' ? 'Renovar' : 'Assinar',
                  style: const TextStyle(fontWeight: FontWeight.bold)),
            ),
        ]),
      );
    });
  }
}
