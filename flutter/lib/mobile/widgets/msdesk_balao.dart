// MSUPTECH_MSDESK_BALOES_V1 (20/10/2026): baloes de passo a passo no celular. O leigo se perdia em
// "Iniciar servico", no aviso de golpe (contagem), na gravacao de tela e na Acessibilidade (Controle de Entrada,
// com a "configuracao restrita" do Android 13+ para app fora da Play Store). Com chave: tem "Entendi" e some para
// sempre naquele aparelho; sem chave: aparece enquanto a situacao pedir (ex.: servico parado).
import 'package:flutter/material.dart';

import '../../models/platform_model.dart';

class MsdeskBalao extends StatefulWidget {
  final String? chave;
  final String titulo;
  final List<String> passos; // **negrito** marcado com dois asteriscos
  final EdgeInsetsGeometry margem;

  const MsdeskBalao(
      {Key? key,
      this.chave,
      required this.titulo,
      required this.passos,
      this.margem = const EdgeInsets.only(top: 8, bottom: 4)})
      : super(key: key);

  @override
  State<MsdeskBalao> createState() => _MsdeskBalaoState();
}

class _MsdeskBalaoState extends State<MsdeskBalao> {
  static const _fundo1 = Color(0xFF1C2A44);
  static const _fundo2 = Color(0xFF0F1A2E);
  static const _ambar = Color(0xFFFFB547);
  late bool _visivel;

  String get _opcao => 'msdesk-balao-${widget.chave}';

  @override
  void initState() {
    super.initState();
    _visivel = widget.chave == null || bind.mainGetLocalOption(key: _opcao) != 'N';
  }

  List<TextSpan> _texto(String s) {
    final partes = s.split('**');
    return [
      for (var i = 0; i < partes.length; i++)
        TextSpan(
            text: partes[i],
            style: i.isOdd
                ? const TextStyle(color: _ambar, fontWeight: FontWeight.w800)
                : null)
    ];
  }

  @override
  Widget build(BuildContext context) {
    if (!_visivel) return const SizedBox.shrink();
    final varios = widget.passos.length > 1;
    return Container(
      width: double.infinity,
      margin: widget.margem,
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 10),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [_fundo1, _fundo2]),
        borderRadius: BorderRadius.circular(14),
        boxShadow: const [
          BoxShadow(color: Color(0x660F1A2E), blurRadius: 18, offset: Offset(0, 8))
        ],
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          const Icon(Icons.lightbulb_outline, color: _ambar, size: 18),
          const SizedBox(width: 8),
          Expanded(
              child: Text(widget.titulo,
                  style: const TextStyle(
                      color: Colors.white,
                      fontSize: 15,
                      fontWeight: FontWeight.w800))),
        ]),
        const SizedBox(height: 6),
        for (var i = 0; i < widget.passos.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 5),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              if (varios)
                Container(
                  width: 20,
                  height: 20,
                  margin: const EdgeInsets.only(right: 8, top: 1),
                  alignment: Alignment.center,
                  decoration: const BoxDecoration(
                      color: Color(0x33FFB547), shape: BoxShape.circle),
                  child: Text('${i + 1}',
                      style: const TextStyle(
                          color: _ambar,
                          fontSize: 11.5,
                          fontWeight: FontWeight.w800)),
                ),
              Expanded(
                child: Text.rich(TextSpan(children: _texto(widget.passos[i])),
                    style: const TextStyle(
                        color: Color(0xFFE8EDF5), fontSize: 13.5, height: 1.4)),
              ),
            ]),
          ),
        if (widget.chave != null)
          Align(
            alignment: Alignment.centerRight,
            child: TextButton(
              style: TextButton.styleFrom(
                  foregroundColor: _ambar,
                  padding: const EdgeInsets.symmetric(horizontal: 10),
                  minimumSize: const Size(0, 34)),
              onPressed: () {
                bind.mainSetLocalOption(key: _opcao, value: 'N');
                setState(() => _visivel = false);
              },
              child: const Text('Entendi',
                  style: TextStyle(fontWeight: FontWeight.w800)),
            ),
          ),
      ]),
    );
  }
}
