"use client";

import React, { useState, useEffect } from 'react';
import { Camera, Cpu, Image, Zap, Upload, Download, Play, ChevronRight, Github, Globe } from 'lucide-react';
import { useRouter } from 'next/navigation';
import NextImage from 'next/image';

const Home = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleStartProject = () => {
    router.push('/photogrammetry');
  };

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900">
      {/* Navigation */}
      <nav className={`fixed top-0 w-full z-50 transition-all duration-300 ${isScrolled ? 'bg-slate-900/95 backdrop-blur-md border-b border-blue-500/20' : 'bg-transparent'
        }`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
                <Camera className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-white">RealFussion</span>
            </div>

            <div className="hidden md:flex items-center space-x-8">
              <button className="text-sm font-medium text-blue-400 transition-colors">
                Inicio
              </button>
              <button
                onClick={() => scrollToSection('features')}
                className="text-sm font-medium text-gray-300 hover:text-white transition-colors"
              >
                Características
              </button>
              <button
                onClick={() => scrollToSection('results')}
                className="text-sm font-medium text-gray-300 hover:text-white transition-colors"
              >
                Resultados
              </button>
              <button
                onClick={handleStartProject}
                className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-6 py-2 rounded-full text-sm font-medium hover:from-blue-700 hover:to-cyan-700 transition-all duration-300 transform hover:scale-105"
              >
                Probar Ahora
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <div className="inline-flex items-center space-x-2 bg-blue-900/50 border border-blue-500/30 rounded-full px-6 py-2 mb-8">
              <Zap className="w-4 h-4 text-blue-400" />
              <span className="text-sm text-blue-300">Tecnología de Vanguardia</span>
            </div>

            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
              RealFussion
              <span className="block bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                Fotogrametría 3D
              </span>
            </h1>

            <p className="text-xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed">
              Transforma imágenes en modelos 3D precisos usando algoritmos avanzados de visión por computadora.
              Experimenta la reconstrucción fotogramétrica de nueva generación con RealFussion.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <button
                onClick={handleStartProject}
                className="group bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-8 py-4 rounded-full text-lg font-medium hover:from-blue-700 hover:to-cyan-700 transition-all duration-300 transform hover:scale-105 flex items-center space-x-2"
              >
                <Play className="w-5 h-5" />
                <span>Comenzar Proyecto</span>
                <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>

              <button className="border border-blue-500/50 text-blue-300 px-8 py-4 rounded-full text-lg font-medium hover:bg-blue-500/10 transition-all duration-300 flex items-center space-x-2">
                <Github className="w-5 h-5" />
                <a href="https://github.com/Fabrizzio20k/REALFUSSION" target="_blank" rel="noopener noreferrer" className="flex items-center space-x-2">
                  <span>Ver Código</span>
                </a>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">Características Principales</h2>
            <p className="text-xl text-gray-400">Tecnologías que impulsan la innovación</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="group bg-slate-800/50 border border-blue-500/20 rounded-2xl p-8 hover:border-blue-500/40 transition-all duration-300 hover:transform hover:scale-105">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Camera className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-4">Captura Inteligente</h3>
              <p className="text-gray-400 leading-relaxed">
                Algoritmos avanzados de detección de características para optimizar
                la captura y correspondencia de puntos clave entre múltiples vistas.
              </p>
            </div>

            <div className="group bg-slate-800/50 border border-blue-500/20 rounded-2xl p-8 hover:border-blue-500/40 transition-all duration-300 hover:transform hover:scale-105">
              <div className="w-12 h-12 bg-gradient-to-r from-cyan-500 to-teal-500 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Cpu className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-4">Procesamiento GPU</h3>
              <p className="text-gray-400 leading-relaxed">
                Aceleración por hardware para reconstrucción 3D en tiempo real,
                optimizado para máximo rendimiento y precisión.
              </p>
            </div>

            <div className="group bg-slate-800/50 border border-blue-500/20 rounded-2xl p-8 hover:border-blue-500/40 transition-all duration-300 hover:transform hover:scale-105">
              <div className="w-12 h-12 bg-gradient-to-r from-indigo-500 to-blue-500 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-4">Resultados Instantáneos</h3>
              <p className="text-gray-400 leading-relaxed">
                Visualización inmediata de modelos 3D con mallas detalladas y
                texturas de alta resolución para análisis profesional.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Results Gallery Section */}
      <section id="results" className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-800/20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">Resultados Fotogramétricos</h2>
            <p className="text-xl text-gray-400">Modelos 3D generados con RealFussion</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Resultados más visibles desde el primer momento */}
            <div className="group relative overflow-hidden rounded-2xl bg-slate-700/30 border border-blue-500/30 hover:border-blue-400/60 transition-all duration-300">
              <div className="aspect-square relative">
                <NextImage
                  src="/res1.png"
                  alt="Modelo 3D - Galleta de gengibre"
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-900/90 via-slate-900/20 to-transparent" />
                <div className="absolute bottom-4 left-4 right-4">
                  <h3 className="text-white font-semibold mb-1">Galleta de gengibre</h3>
                  <p className="text-blue-300 text-sm">60 imágenes • 155.65 segundos</p>
                </div>
                <div className="absolute top-4 right-4">
                  <div className="bg-blue-500/80 backdrop-blur-sm text-white text-xs px-2 py-1 rounded-full">
                    3D Model
                  </div>
                </div>
              </div>
            </div>

            <div className="group relative overflow-hidden rounded-2xl bg-slate-700/30 border border-blue-500/30 hover:border-blue-400/60 transition-all duration-300">
              <div className="aspect-square relative">
                <NextImage
                  src="/res2.png"
                  alt="Modelo 3D - Cabeza de Budha"
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-900/90 via-slate-900/20 to-transparent" />
                <div className="absolute bottom-4 left-4 right-4">
                  <h3 className="text-white font-semibold mb-1">Cabeza de Budha</h3>
                  <p className="text-blue-300 text-sm">67 imágenes • 105.67 segundos </p>
                </div>
                <div className="absolute top-4 right-4">
                  <div className="bg-cyan-500/80 backdrop-blur-sm text-white text-xs px-2 py-1 rounded-full">
                    HD Texture
                  </div>
                </div>
              </div>
            </div>

            <div className="group relative overflow-hidden rounded-2xl bg-slate-700/30 border border-blue-500/30 hover:border-blue-400/60 transition-all duration-300">
              <div className="aspect-square relative">
                <NextImage
                  src="/res3.png"
                  alt="Modelo 3D - Estatua de Jesús"
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-900/90 via-slate-900/20 to-transparent" />
                <div className="absolute bottom-4 left-4 right-4">
                  <h3 className="text-white font-semibold mb-1">Estatua de Jesús</h3>
                  <p className="text-blue-300 text-sm">40 imágenes • 88.24 segundos</p>
                </div>
                <div className="absolute top-4 right-4">
                  <div className="bg-teal-500/80 backdrop-blur-sm text-white text-xs px-2 py-1 rounded-full">
                    Historical
                  </div>
                </div>
              </div>
            </div>

            <div className="group relative overflow-hidden rounded-2xl bg-slate-700/30 border border-blue-500/30 hover:border-blue-400/60 transition-all duration-300">
              <div className="aspect-square relative">
                <NextImage
                  src="/res4.png"
                  alt="Modelo 3D - Aguila"
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-900/90 via-slate-900/20 to-transparent" />
                <div className="absolute bottom-4 left-4 right-4">
                  <h3 className="text-white font-semibold mb-1">Águila</h3>
                  <p className="text-blue-300 text-sm">39 imágenes • 63.49 segundos</p>
                </div>
                <div className="absolute top-4 right-4">
                  <div className="bg-indigo-500/80 backdrop-blur-sm text-white text-xs px-2 py-1 rounded-full">
                    Animal
                  </div>
                </div>
              </div>
            </div>

            <div className="group relative overflow-hidden rounded-2xl bg-slate-700/30 border border-blue-500/30 hover:border-blue-400/60 transition-all duration-300">
              <div className="aspect-square relative">
                <NextImage
                  src="/res5.png"
                  alt="Modelo 3D - Craneo Humano"
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-900/90 via-slate-900/20 to-transparent" />
                <div className="absolute bottom-4 left-4 right-4">
                  <h3 className="text-white font-semibold mb-1">Craneo Humano</h3>
                  <p className="text-blue-300 text-sm">47 imágenes • 77.28 segundos</p>
                </div>
                <div className="absolute top-4 right-4">
                  <div className="bg-blue-600/80 backdrop-blur-sm text-white text-xs px-2 py-1 rounded-full">
                    Object
                  </div>
                </div>
              </div>
            </div>

            <div className="group relative overflow-hidden rounded-2xl bg-slate-700/30 border border-blue-500/30 hover:border-blue-400/60 transition-all duration-300">
              <div className="aspect-square relative">
                <NextImage
                  src="/res6.png"
                  alt="Modelo 3D - Escultura de Pato"
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-900/90 via-slate-900/20 to-transparent" />
                <div className="absolute bottom-4 left-4 right-4">
                  <h3 className="text-white font-semibold mb-1">Escultura de Pato</h3>
                  <p className="text-blue-300 text-sm">53 imágenes • 130.23 segundos</p>
                </div>
                <div className="absolute top-4 right-4">
                  <div className="bg-cyan-600/80 backdrop-blur-sm text-white text-xs px-2 py-1 rounded-full">
                    Historical
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Workflow Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">Flujo de Trabajo</h2>
            <p className="text-xl text-gray-400">Del concepto al modelo 3D en simples pasos</p>
          </div>

          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full flex items-center justify-center mx-auto mb-6">
                <Upload className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">1. Cargar Imágenes</h3>
              <p className="text-gray-400">Sube múltiples fotografías del objeto desde diferentes ángulos</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-cyan-500 to-teal-500 rounded-full flex items-center justify-center mx-auto mb-6">
                <Cpu className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">2. Procesamiento</h3>
              <p className="text-gray-400">Los algoritmos analizan y correlacionan puntos característicos</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-teal-500 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <Image className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">3. Reconstrucción</h3>
              <p className="text-gray-400">Generación automática de la geometría y textura 3D</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <Download className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">4. Exportar</h3>
              <p className="text-gray-400">Descarga el modelo en formatos estándar de la industria</p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-blue-900/20 to-cyan-900/20">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-white mb-2">96.8%</div>
              <div className="text-gray-400">Precisión Promedio</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-white mb-2">~ 2 min</div>
              <div className="text-gray-400">Tiempo de Procesamiento</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-white mb-2">20+</div>
              <div className="text-gray-400">Modelos Generados</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-white mb-2">2K</div>
              <div className="text-gray-400">Resolución Máxima</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-6">
            ¿Listo para crear tu primer modelo 3D?
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            Experimenta la potencia de RealFussion y la fotogrametría computacional de próxima generación
          </p>
          <button
            onClick={handleStartProject}
            className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-12 py-4 rounded-full text-lg font-medium hover:from-blue-700 hover:to-cyan-700 transition-all duration-300 transform hover:scale-105"
          >
            Comenzar Ahora
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-blue-500/20 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
                <Camera className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-white">RealFussion</span>
            </div>

            <div className="flex items-center space-x-6 text-gray-400">
              <span className="text-sm">© 2025 RealFussion - Proyecto de Gráficos Computacionales</span>
              <div className="flex items-center space-x-4">
                <a href="https://github.com/Fabrizzio20k/REALFUSSION" target="_blank" rel="noopener noreferrer">
                  <Github className="w-5 h-5 hover:text-white cursor-pointer transition-colors" />
                </a>
                <Globe className="w-5 h-5 hover:text-white cursor-pointer transition-colors" />
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;